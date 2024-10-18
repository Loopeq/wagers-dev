import asyncio
import datetime
import math
from datetime import timedelta
import random

from typing import List, Optional

from asyncpg import ForeignKeyViolationError
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy import Integer, cast, func, insert, inspect, or_, select, text, desc, update, exists, delete
from sqlalchemy.orm import aliased, contains_eager, joinedload, selectinload, object_session, ORMExecuteState
from sqlalchemy import and_
from sqlalchemy.sql.expression import func
from sqlalchemy.util import await_only

from src.data.schemas import (MatchDTO, SportDTO, LeagueDTO,
                              MatchMemberDTO, MatchMemberAddDTO,
                              BetDTO, BetAddDTO,
                              MatchUpcomingDTO, BetChangeAddDTO)
from src.data.models import Sport, League, Match, MatchMember, MatchResultEnum, MatchSideEnum, \
    BetTypeEnum, Bet, BetStatusEnum, BetChange
from src.data.database import Base, async_engine, async_session_factory
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_object_session, AsyncSession
from sqlalchemy import case, literal_column
from sqlalchemy.orm import Session


async def create_tables():
    async with async_engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


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
                raise


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


class UpdateManager:

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
                func.abs(b_old.point - b_new.point) != 0,
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
