import asyncio
import datetime
from datetime import timedelta
from typing import List, Optional, AsyncGenerator
from fastapi import Depends
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, exists, not_
from sqlalchemy.orm import aliased
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql.expression import func

from src.data.schemas import (MatchDTO, SportDTO, LeagueDTO,
                              MatchMemberAddDTO,
                              BetAddDTO,
                              MatchUpcomingDTO)
from src.data.models import Sport, League, Match, MatchMember, \
    Bet, BetChange, User, MatchResult
from src.data.database import async_session_factory
from sqlalchemy.ext.asyncio import AsyncSession


class MatchOrm:
    @staticmethod
    async def insert_match(match: MatchDTO):
        async with async_session_factory() as session:
            try:
                match_orm = Match(id=match.id, league_id=match.league_id, start_time=match.start_time)
                session.add(match_orm)
                await session.commit()
            except IntegrityError as e:
                if 'foreign key constraint' in str(e.orig):
                    raise ValueError(f'League with id {match.league_id} does not exist.')
                await session.rollback()

    @staticmethod
    async def get_upcoming_matches(start_timedelta: Optional[timedelta] = None,
                                   end_timedelta: Optional[timedelta] = None) -> (
            List)[MatchUpcomingDTO]:
        async with async_session_factory() as session:
            current_time = datetime.datetime.utcnow()
            query = select(Match.start_time, Match.id)

            if start_timedelta:
                query = query.filter(Match.start_time > current_time + start_timedelta)
            if end_timedelta:
                query = query.filter(Match.start_time <= current_time + end_timedelta, Match.start_time > current_time)

            result = await session.execute(query)
            matches = result.fetchall()
            matches_dto = [MatchUpcomingDTO.model_validate(row, from_attributes=True) for row in matches]
            return matches_dto

    @staticmethod
    async def exists_match_by_id(match_id: int) -> bool:
        async with async_session_factory() as session:
            query = select(Match.id).filter(Match.id == match_id)
            result = await session.execute(query)
            return result.scalar() is not None

    @staticmethod
    async def get_matches_ready_to_results():
        lg = aliased(League)
        async with async_session_factory() as session:
            now = datetime.datetime.utcnow()
            sub_query = select(Match.id, Match.league_id).filter(Match.start_time < now,
                                                                 (Match.start_time + timedelta(days=2)) > now,
                                                                 (Match.start_time + timedelta(
                                                                     hours=3)) < now).subquery()

            stmt = select(sub_query.c.id, lg.id).select_from(sub_query).join(lg, lg.id == sub_query.c.league_id) \
                .filter(
                ~exists(
                    select(1).select_from(MatchResult).filter(MatchResult.match_id == sub_query.c.id)
                ))

            result = await session.execute(stmt)
            return result.fetchall()


class MatchMemberOrm:
    @staticmethod
    async def insert_match_member(match_member: MatchMemberAddDTO):
        async with async_session_factory() as session:
            try:
                match_member_orm = MatchMember(match_id=match_member.match_id, name=match_member.name,
                                               status=match_member.status,
                                               side=match_member.side)
                session.add(match_member_orm)
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                if 'foreign key constraint' in str(e.orig):
                    raise ValueError(f'Match with id {match_member.match_id} does not exist.')
            except Exception:
                await session.rollback()


class SportOrm:
    @staticmethod
    async def insert_sport(sport: SportDTO):
        async with async_session_factory() as session:
            try:
                sport_orm = Sport(id=sport.id, name=sport.name)
                session.add(sport_orm)
                await session.commit()
            except IntegrityError:
                await session.rollback()
            except Exception:
                await session.rollback()

    @staticmethod
    async def fetch_sports():
        async with async_session_factory() as session:
            stmt = await session.execute(select(Sport))
            result = stmt.scalars().all()
            result_dto = [SportDTO.model_validate(row, from_attributes=True) for row in result]
            return result_dto


class LeagueOrm:

    @staticmethod
    async def insert_league(league: LeagueDTO):
        async with async_session_factory() as session:
            try:
                league_orm = League(id=league.id, sport_id=league.sport_id, name=league.name)
                session.add(league_orm)
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                if 'foreign key constraint' in str(e.orig):
                    raise ValueError(f'Sport with id {league.sport_id} does not exist.')
            except Exception:
                session.rollback()


class UpdateManager:
    @staticmethod
    async def insert_match(sport, league, match, mm_home, mm_away):
        async with async_session_factory() as session:
            async with session.begin():
                await session.execute(insert(Sport).values(
                    id=sport.id, name=sport.name).on_conflict_do_nothing())
                await session.execute(insert(League).values(
                    id=league.id,
                    sport_id=league.sport_id,
                    name=league.name).on_conflict_do_nothing())
                await session.execute(
                    insert(Match).values(
                        id=match.id,
                        league_id=match.league_id,
                        start_time=match.start_time).on_conflict_do_nothing())
                await session.execute(insert(MatchMember).values(
                    match_id=mm_home.match_id,
                    name=mm_home.name,
                    status=mm_home.status,
                    side=mm_home.side).on_conflict_do_nothing())
                await session.execute(insert(MatchMember).values(
                    match_id=mm_away.match_id,
                    name=mm_away.name,
                    status=mm_away.status,
                    side=mm_away.side).on_conflict_do_nothing())

    @staticmethod
    async def insert_bets(bets: List[BetAddDTO]):
        async with (async_session_factory() as session):

            if not bets:
                return

            match_id = bets[0].match_id
            stmt = await session.execute(
                select(func.max(Bet.version))
                .select_from(Bet)
                .filter(Bet.match_id == bets[0].match_id))
            version = stmt.fetchone()[0]

            if not version:
                version = 0

            bets_orm = [Bet(match_id=match_id,
                            point=bet.point,
                            home_cf=bet.home_cf,
                            away_cf=bet.away_cf,
                            type=bet.type,
                            period=bet.period,
                            created_at=bet.created_at,
                            version=version + 1)
                        for bet in bets]

            session.add_all(bets_orm)
            await session.commit()

            b_new = aliased(Bet)
            b_old = aliased(Bet)

            query = (select(b_old.id, b_new.id)
                     .select_from(b_old)
                     .join(b_new, and_(b_old.version == version,
                                       b_old.type == b_new.type,
                                       b_old.period == b_new.period)))

            query = query.filter(
                b_old.point != b_new.point,
                b_new.version == version + 1,
                b_old.match_id == match_id,
                b_new.match_id == match_id
            )

            result = await session.execute(query)
            not_equals = result.fetchall()

            if not_equals:
                bet_changes = [BetChange(old_bet_id=nq[0], new_bet_id=nq[1]) for nq in not_equals]
                session.add_all(bet_changes)

            await session.commit()


class UserOrm:

    @staticmethod
    async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_factory() as session:
            yield session

    @staticmethod
    async def get_user_db(session: AsyncSession = Depends(get_async_session)):
        async for db_session in session:
            yield SQLAlchemyUserDatabase(db_session, User)


async def _dev():
    res = await MatchOrm.get_matches_ready_to_results()
    for match in res:
        print(match)



if __name__ == "__main__":
    asyncio.run(_dev())
