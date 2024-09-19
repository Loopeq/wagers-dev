import asyncio
import datetime
from datetime import timedelta

from typing import List, Optional

from asyncpg import ForeignKeyViolationError
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy import Integer, and_, cast, func, insert, inspect, or_, select, text, desc
from sqlalchemy.orm import aliased, contains_eager, joinedload, selectinload, object_session
from sqlalchemy import and_
from sqlalchemy.sql.expression import func

from src.data.schemas import (MatchDTO, MatchRelDTO, SportDTO, SportRelDTO, LeagueDTO, LeagueRelDTO,
                              MatchMemberDTO, MatchMemberAddDTO, MatchMemberRelDTO,
                              BetDTO, BetAddDTO, BetRelDTO, BetValueDTO, BetValueAddDTO, BetValueRelDTO,
                              MatchUpcomingDTO)
from src.data.models import Sport, League, Match, MatchMember, MatchResultEnum, MatchSideEnum, BetTypeEnum, Bet, \
    BetValue, BetStatusEnum
from src.data.database import Base, async_engine, async_session_factory
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_object_session, AsyncSession

from src.data.database import async_session_factory
from src.data.models import BetValue, Bet


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

    @staticmethod
    async def get_upcoming_matches(start_timedelta: timedelta, end_timedelta: Optional[timedelta] = None) -> List[MatchUpcomingDTO]:
        """ Возвращает (id, start_time) матчей, которые еще не начались, либо до них остается < timedelta"""
        async with async_session_factory() as session:
            current_time = datetime.datetime.utcnow()
            query = select(Match.start_time, Match.id).filter(Match.start_time > current_time + start_timedelta)
            if end_timedelta:
                query = query.filter(Match.start_time <= current_time + end_timedelta)
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

    @staticmethod
    async def get_match_members_by_match_id(match_id: int,
                                            relation: bool = False) -> List[MatchMemberRelDTO] | List[MatchMemberDTO]:
        async with async_session_factory() as session:
            query = select(MatchMember).where(MatchMember.match_id == match_id)

            if relation:
                query = query.options(selectinload(MatchMember.match), selectinload(MatchMember.bets))

            result = await session.execute(query)
            match_member = result.scalars().fetchall()
            model_to_validate = MatchMemberRelDTO if relation else MatchMemberDTO
            match_member_dto = [model_to_validate.model_validate(row, from_attributes=True) for row in match_member]
            return match_member_dto


class BetOrm:
    @staticmethod
    async def insert_bet(bet: BetAddDTO):
        async with async_session_factory() as session:
            try:
                bet_orm = Bet(match_id=bet.match_id, type=bet.type,
                              period=bet.period)
                session.add(bet_orm)
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                if 'foreign key constraint' in str(e.orig):
                    raise ValueError(f'Match with id {bet.match_id} does not exist.')
            except Exception:
                await session.rollback()
                raise

    @staticmethod
    async def insert_bets(bets: List[BetAddDTO]):
        async with async_session_factory() as session:
            try:
                bets_orm = [Bet(match_id=bet_dto.match_id, type=bet_dto.type, period=bet_dto.period) for bet_dto in
                            bets]
                session.add_all(bets_orm)
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                if 'foreign key constraint' in str(e.orig):
                    raise ValueError(f'Match with id {bets[0].match_id} does not exist')
            except Exception:
                await session.rollback()
                raise

    @staticmethod
    async def get_bet_id_by_(bet_type: BetTypeEnum, period: int, match_id: int):
        async with async_session_factory() as session:
            query = select(Bet.id).select_from(Bet).filter(and_(Bet.type == bet_type.value, Bet.period == period,
                                                                Bet.match_id == match_id))
            result = await session.execute(query)
            bet_id = result.fetchone()
            return bet_id[0]

    @staticmethod
    async def get_bet_by_id(id: int) -> BetRelDTO:
        async with async_session_factory() as session:
            query = select(Bet).options((selectinload(Bet.match)), (selectinload(Bet.bet_values))).where(Bet.id == id)
            result = await session.execute(query)
            bet = result.scalars().one()
            bet_dto = BetRelDTO.model_validate(bet, from_attributes=True)
            return bet_dto


class BetValueOrm:
    @staticmethod
    async def insert_bet_values(bet_values: List[List[BetValueAddDTO]]):
        async with async_session_factory() as session:
            try:
                bets_orm = []
                for bet_group in bet_values:
                    version = await BetValueOrm.get_bet_value_version(bet_group[0].bet_id)
                    for bet_value_dto in bet_group:
                        bets_orm.append(BetValue(bet_id=bet_value_dto.bet_id, value=bet_value_dto.value,
                                                 point=bet_value_dto.point,
                                                 created_at=bet_value_dto.created_at,
                                                 status=bet_value_dto.status,
                                                 type=bet_value_dto.type,
                                                 version=version+1))
                session.add_all(bets_orm)
                await session.commit()

            except IntegrityError as e:
                session.add_all(bets_orm)
                await session.commit()
                await session.rollback()
                if 'foreign key constraint' in str(e.orig):
                    raise ValueError(f'Bet with id {bet_value.bet_id} does not exist.')
            except Exception:
                await session.rollback()
                raise

    @staticmethod
    async def get_bet_values_by_bet_id(bet_id: int) -> List[BetValueRelDTO]:
        async with async_session_factory() as session:
            query = (select(BetValue).options(selectinload(BetValue.bet)).where(BetValue.bet_id == bet_id))
            result = await session.execute(query)
            bet_values = result.scalars().all()
            bet_values_orm = [BetValueRelDTO.model_validate(row, from_attributes=True) for row in bet_values]
            return bet_values_orm

    @staticmethod
    async def get_bet_values() -> List[BetValueRelDTO]:
        async with async_session_factory() as session:
            query = select(BetValue).options(selectinload(BetValue.bet))
            result = await session.execute(query)
            bet_values = result.scalars().all()
            bet_values_orm = [BetValueRelDTO.model_validate(row, from_attributes=True) for row in bet_values]
            return bet_values_orm

    @staticmethod
    async def get_bet_value_version(bet_id) -> int:
        async with async_session_factory() as session:
            query = select(BetValue.version).where(BetValue.bet_id == bet_id)
            result = await session.execute(query)
            versions = result.fetchall()
            if not versions:
                return 1
            return max(versions)[0]

    @staticmethod
    async def get_current_values(bet_id) -> List[BetValueDTO]:
        async with async_session_factory() as session:

            subquery = (
                select(func.max(BetValue.version))
                .where(BetValue.bet_id == bet_id)
                .scalar_subquery()
            )

            query = (
                select(BetValue)
                .where(BetValue.version == subquery)
            )

            result = await session.execute(query)
            bet_values = result.scalars().all()
            return [BetValueDTO.model_validate(row, from_attributes=True) for row in bet_values]


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
                raise

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


class UpdateManager:

    @staticmethod
    async def on_point_change():
        async with (async_session_factory() as session):
            query = text("""
            WITH LastTwoVersions AS (
                SELECT 
                    bet_id, 
                    version
                FROM bet_value
                GROUP BY bet_id, version
                HAVING version IN (
                    SELECT DISTINCT version
                    FROM bet_value bv
                    WHERE bv.bet_id = bet_value.bet_id
                    ORDER BY version DESC
                    LIMIT 2
                )
            ),

            MedianValues AS (
                SELECT 
                    bet_value.bet_id AS bi, 
                    bet_value.version AS v, 
                    percentile_disc(0.5) WITHIN GROUP (ORDER BY bet_value.point) AS median_point
                FROM bet_value
                JOIN LastTwoVersions 
                    ON bet_value.bet_id = LastTwoVersions.bet_id 
                    AND bet_value.version = LastTwoVersions.version
                WHERE bet_value.point IS NOT NULL AND bet_value.point > 0
                GROUP BY bet_value.bet_id, bet_value.version
            )

            SELECT bi, v, median_point
            FROM MedianValues
            WHERE bi IN (
                SELECT bi
                FROM MedianValues
                GROUP BY bi
                HAVING COUNT(DISTINCT median_point) > 1
            )
            ORDER BY bi, v;
            """)

            result = await session.execute(query)
            return result.fetchall()


async def main():
    res = await UpdateManager.on_point_change()
    print(res)

if __name__ == '__main__':
    asyncio.run(main())
