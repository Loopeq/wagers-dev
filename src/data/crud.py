import asyncio
import datetime
from datetime import timedelta
from typing import List

from asyncpg import ForeignKeyViolationError
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy import Integer, and_, cast, func, insert, inspect, or_, select, text
from sqlalchemy.orm import aliased, contains_eager, joinedload, selectinload
from src.data.schemas import (MatchDTO, MatchRelDTO, SportDTO, SportRelDTO, LeagueDTO, LeagueRelDTO,
                              MatchMemberDTO, MatchMemberAddDTO, MatchMemberRelDTO)
from src.data.models import Sport, League, Match, MatchMember, MatchResultEnum, MatchSideEnum, BetTypeEnum, Bet, \
    BetValue
from src.data.database import Base, async_engine, async_session_factory


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
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
    async def get_matches() -> List[MatchRelDTO]:
        async with async_session_factory() as session:
            query = (select(Match).options(selectinload(Match.league), selectinload(Match.match_members)))
            result = await session.execute(query)
            matches = result.scalars().all()
            matches_dto = [MatchRelDTO.model_validate(row, from_attributes=True) for row in matches]
            return matches_dto

    @staticmethod
    async def get_match_by_id(id: int) -> MatchRelDTO | None:
        async with async_session_factory() as session:
            query = (select(Match)
                     .options(
                selectinload(Match.league),
                selectinload(Match.match_members)).where(Match.id == id))
            result = await session.execute(query)
            match = result.scalars().first()
            if not match:
                return None
            sport_dto = MatchRelDTO.model_validate(match, from_attributes=True)
            return sport_dto


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

    @staticmethod
    async def get_match_members_by_match_id(match_id: int) -> List[MatchMemberRelDTO]:
        async with async_session_factory() as session:
            query = (select(MatchMember)
                     .options(selectinload(MatchMember.match), selectionload(MatchMember.bets))
                     .where(MatchMember.match_id == match_id))
            result = await session.execute(query)
            match_member = result.scalars().fetchall()
            match_member_dto = [MatchMemberRelDTO.model_validate(row, from_attributes=True) for row in match_member]
            assert len(match_member_dto) == 2
            return match_member_dto


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

    @staticmethod
    async def get_sports() -> List[SportRelDTO]:
        async with async_session_factory() as session:
            query = (select(Sport).options(selectinload(Sport.leagues)))
            result = await session.execute(query)
            sports = result.scalars().all()
            sports_dto = [SportRelDTO.model_validate(row, from_attributes=True) for row in sports]
            return sports_dto

    @staticmethod
    async def get_sport_by_id(id: int) -> SportRelDTO | None:
        async with async_session_factory() as session:
            query = (select(Sport).options(selectinload(Sport.leagues)).where(Sport.id == id))
            result = await session.execute(query)
            sport = result.scalars().first()
            if not sport:
                return None
            sport_dto = SportRelDTO.model_validate(sport, from_attributes=True)
            return sport_dto

    @staticmethod
    async def delete_sport(sport: SportDTO):
        async with async_session_factory() as session:
            sport_orm = await session.get(Sport, sport.id)
            if sport_orm is not None:
                await session.delete(sport_orm)
                await session.commit()
            else:
                raise ValueError(f'Sport({sport.id}, {sport.name}) does not exist.')


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

    @staticmethod
    async def get_leagues() -> List[LeagueRelDTO]:
        async with async_session_factory() as session:
            query = (select(League).options(selectinload(League.matches), selectinload(League.sport)))
            result = await session.execute(query)
            leagues = result.scalars().all()
            leagues_dto = [LeagueRelDTO.model_validate(row, from_attributes=True) for row in leagues]
            return leagues_dto

    @staticmethod
    async def get_league_by_id(id: int) -> LeagueRelDTO | None:
        async with async_session_factory() as session:
            query = (select(League)
                     .options(selectinload(League.matches),
                              selectinload(League.sport))
                     .where(League.id == id))
            result = await session.execute(query)
            league = result.scalars().first()
            if not league:
                return None
            league_dto = LeagueRelDTO.model_validate(league, from_attributes=True)
            return league_dto


async def main():
    await LeagueOrm.insert_league(LeagueDTO(id=3, sport_id=2, name='NBA'))
    await LeagueOrm.insert_league(LeagueDTO(id=4, sport_id=1, name='WWE'))
    await MatchOrm.insert_match(MatchDTO(id=12, league_id=3,
                                         start_time=datetime.datetime.utcnow() + timedelta(minutes=30)))
    await MatchOrm.insert_match(MatchDTO(id=15, league_id=4,
                                         start_time=datetime.datetime.utcnow() + timedelta(minutes=20)))

    res = await MatchOrm.get_matches()

    res1 = await MatchOrm.get_match_by_id(12)
    res2 = await MatchOrm.get_match_by_id(34)

    matchMember = (MatchMemberAddDTO(match_id=2, name='Dinamp', side=MatchSideEnum.home), )


if __name__ == '__main__':
    asyncio.run(main())
