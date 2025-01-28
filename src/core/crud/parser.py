import datetime
from datetime import timedelta
from typing import List, Optional
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, exists
from sqlalchemy.orm import aliased
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql.expression import func

from src.core.db.db_helper import db_helper
from src.core.schemas import (MatchDTO, SportDTO, LeagueDTO,
                              MatchMemberAddDTO,
                              BetAddDTO,
                              MatchUpcomingDTO)
from src.core.models import Sport, League, Match, MatchMember, \
    Bet, BetChange, MatchResult


class MatchOrm:
    @staticmethod
    async def insert_match(match: MatchDTO):
        async with db_helper.session_factory() as session:
            try:
                match_orm = Match(id=match.id, league_id=match.league_id, start_time=match.start_time)
                session.add(match_orm)
                await session.commit()
            except IntegrityError as e:
                if 'foreign key constraint' in str(e.orig):
                    raise ValueError(f'League with id {match.league_id} does not exist.')
                await session.rollback()

    @staticmethod
    async def get_matches_ready_to_results():
        async with db_helper.session_factory() as session:
            lg = aliased(League)
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
        async with db_helper.session_factory() as session:
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
        async with db_helper.session_factory() as session:
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
        async with db_helper.session_factory() as session:
            stmt = await session.execute(select(Sport))
            result = stmt.scalars().all()
            result_dto = [SportDTO.model_validate(row, from_attributes=True) for row in result]
            return result_dto


class LeagueOrm:
    @staticmethod
    async def insert_league(league: LeagueDTO):
        async with db_helper.session_factory() as session:
            try:
                league_orm = League(id=league.id, sport_id=league.sport_id, name=league.name)
                session.add(league_orm)
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                if 'foreign key constraint' in str(e.orig):
                    raise ValueError(f'Sport with id {league.sport_id} does not exist.')
            except Exception:
                await session.rollback()


class UpdateManager:

    @staticmethod
    async def insert_bets(bets: List[BetAddDTO]):
        async with db_helper.session_factory() as session:
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
