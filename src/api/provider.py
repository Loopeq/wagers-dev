import asyncio
import datetime
from datetime import timedelta
from typing import Optional, List
from sqlalchemy import select, text, func, literal_column
from sqlalchemy.orm import aliased
from sqlalchemy.sql.functions import coalesce
from sqlalchemy import and_
from src.api.schemas import FilterRequest, ValueFilterType
from src.api.utils import justify_changes
from src.data.database import async_session_factory
from src.data.models import Match, Bet, BetChange, League, MatchMember
import json
from src.data.schemas import BetDTO
from src.parser.calls.event_details import get_match_details


class ApiOrm:

    @staticmethod
    async def get_match_history_by_team_name(team_name: str, current_match_id: int):
        async with async_session_factory() as session:
            mm = aliased(MatchMember)
            query = select(mm.match_id).select_from(mm).filter(mm.name == team_name,
                                                               mm.match_id != current_match_id)
            match_ids = await session.execute(query)

            mm_home = aliased(MatchMember)
            mm_away = aliased(MatchMember)
            m = aliased(Match)
            history = []
            for match_id in match_ids.fetchall():
                query = select(m.id, mm_home.name, mm_away.name, m.start_time) \
                    .select_from(m).join(mm_home, and_(mm_home.match_id == match_id[0], mm_home.side == 'home')) \
                    .join(mm_away, and_(mm_away.match_id == match_id[0], mm_away.side == 'away')) \
                    .filter(m.id == match_id[0], m.start_time < datetime.datetime.utcnow())
                result = await session.execute(query)

                info = result.fetchone()
                
                if info:
                    match_details = await get_match_details(match_id[0])
                    if match_details:
                        details = [{'number': detail.get('number'),
                                    'team_1_score': detail.get('team_1_score'),
                                    'team_2_score': detail.get('team_2_score')} for detail in match_details]
                    else:
                        details = None

                    info = {'match_id': info[0], 'home_name': info[1], 'away_name': info[2], 'start_time': info[3],
                            'details': details}

                    history.append(info)
            return history

    @staticmethod
    async def get_initial_points(match_id: int) -> List[BetDTO]:
        async with async_session_factory() as session:
            bet = aliased(Bet)
            initial_change_query = select(bet).select_from(bet) \
                .filter(bet.match_id == match_id, bet.version == 1)
            initial_change = await session.execute(initial_change_query)
            initial_change_orm = initial_change.scalars().all()
            initial_change_dto = [BetDTO.model_validate(row, from_attributes=True) for row in initial_change_orm]
            return initial_change_dto

    @staticmethod
    async def get_last_points(match_id: int) -> List[BetDTO]:
        async with async_session_factory() as session:
            bet = aliased(Bet)
            version = await session.execute(
                select(func.max(bet.version))
                .select_from(bet)
                .filter(bet.match_id == match_id))
            version = version.fetchone()[0]

            if version == 1:
                return []

            last_change_query = select(bet).select_from(bet) \
                .filter(bet.match_id == match_id, bet.version == version)
            last_change = await session.execute(last_change_query)
            last_change_orm = last_change.scalars().all()
            last_change_dto = [BetDTO.model_validate(row, from_attributes=True) for row in last_change_orm]
            return last_change_dto

    @staticmethod
    async def get_point_change(match_id: int):
        async with async_session_factory() as session:
            bc = aliased(BetChange)
            old_b = aliased(Bet)
            new_b = aliased(Bet)
            m = aliased(Match)
            mm_home = aliased(MatchMember)
            mm_away = aliased(MatchMember)
            le = aliased(League)
            change_query = select(old_b.home_cf,
                                  new_b.home_cf,
                                  old_b.away_cf,
                                  new_b.away_cf,
                                  old_b.point,
                                  new_b.point,
                                  old_b.type,
                                  old_b.period,
                                  new_b.created_at) \
                .select_from(bc) \
                .join(old_b, old_b.id == bc.old_bet_id) \
                .join(new_b, new_b.id == bc.new_bet_id) \
                .filter(old_b.match_id == match_id,
                        new_b.match_id == match_id) \
                .order_by(new_b.created_at.desc())

            match_query = select(m.id,
                                 mm_home.id,
                                 mm_home.name,
                                 mm_away.id,
                                 mm_away.name,
                                 m.start_time,
                                 le.name,
                                 ). \
                select_from(m). \
                join(le, le.id == m.league_id, isouter=True). \
                join(mm_home, and_(mm_home.match_id == m.id, mm_home.side == 'home'), isouter=True). \
                join(mm_away, and_(mm_away.match_id == m.id, mm_away.side == 'away'), isouter=True). \
                filter(m.id == match_id)

            changes = await session.execute(change_query)
            match = await session.execute(match_query)
            match = match.fetchone()
            initial_points = await ApiOrm.get_initial_points(match_id)

            start_time = match[5]
            changes = [{'old_home_cf': change[0],
                        'new_home_cf': change[1],
                        'old_away_cf': change[2],
                        'new_away_cf': change[3],
                        'old_point': change[4],
                        'new_point': change[5],
                        'type': change[6],
                        'period': change[7],
                        'created_at': change[8]} for change in changes.fetchall()]

            data = {
                'initial_points': [{
                    'home_cf': ipoint.home_cf,
                    'away_cf': ipoint.away_cf,
                    'point': ipoint.point,
                    'type': ipoint.type,
                    'period': ipoint.period,
                    'created_at': ipoint.created_at
                } for ipoint in initial_points],
                'match': {
                    'match_id': match[0],
                    'home_id': match[1],
                    'home_name': match[2],
                    'away_id': match[3],
                    'away_name': match[4],
                    'start_time': start_time,
                    'league_name': match[6],
                },
                'changes': changes}

            return data

    @staticmethod
    async def get_ini_last_points(match_id):
        async with (async_session_factory() as session):
            ini_bet = aliased(Bet)
            last_bet = aliased(Bet)

            max_version = await session.execute(
                select(func.max(ini_bet.version))
                .select_from(ini_bet)
                .filter(ini_bet.match_id == match_id))
            max_version = max_version.fetchone()[0]

            query = select(ini_bet.type, ini_bet.period, ini_bet.point, last_bet.point, ).select_from(ini_bet).join(
                last_bet, and_(
                    last_bet.version == max_version,
                    last_bet.match_id == match_id,
                    last_bet.type == ini_bet.type,
                    last_bet.period == ini_bet.period)
            ).filter(func.abs(last_bet.point - ini_bet.point) != 0, ini_bet.match_id == match_id,
                     ini_bet.version == 1).order_by(ini_bet.period, ini_bet.type)

            changes = await session.execute(query)
            changes = changes.fetchall()
            return changes

    @staticmethod
    async def get_match_with_change(filters: FilterRequest):
        async with async_session_factory() as session:
            m = aliased(Match)
            bc = aliased(BetChange)
            le = aliased(League)
            b = aliased(Bet)
            mm_home = aliased(MatchMember)
            mm_away = aliased(MatchMember)

            subquery = select(m.id.label('match_id'),
                              func.count(bc.id).label('change_count'),
                              func.max(b.created_at).label('last_change_time')). \
                join(b, b.match_id == m.id). \
                join(bc, bc.new_bet_id == b.id). \
                group_by(m.id).subquery()

            query = select(m.id,
                           mm_home.id,
                           mm_home.name,
                           mm_away.id,
                           mm_away.name,
                           m.start_time,
                           le.name,
                           coalesce(subquery.c.change_count, 0),
                           subquery.c.last_change_time
                           ). \
                select_from(m). \
                join(le, le.id == m.league_id, isouter=True). \
                join(mm_home, and_(mm_home.match_id == m.id, mm_home.side == 'home'), isouter=True). \
                join(mm_away, and_(mm_away.match_id == m.id, mm_away.side == 'away'), isouter=True). \
                join(subquery, subquery.c.match_id == m.id, isouter=True)

            if filters.not_null_point:
                query = query.filter(subquery.c.change_count != 0)

            if (filters.finished is None) and (filters.hour is None):
                query = query.filter(m.start_time >= datetime.datetime.utcnow())
            elif filters.finished:
                query = query.filter(m.start_time < datetime.datetime.utcnow()).limit(10)
            elif filters.hour:
                query = query.filter(
                    and_(m.start_time <= datetime.datetime.utcnow() + timedelta(hours=filters.hour),
                         m.start_time >= datetime.datetime.utcnow()))

            query = query.group_by(m.id, mm_home.id, mm_home.name, mm_away.id, mm_home.name, m.start_time, le.name,
                                   subquery.c.change_count, subquery.c.last_change_time)

            if filters.filter == ValueFilterType.match_start_time:
                query = query.order_by(m.start_time.asc())
            elif filters.filter == ValueFilterType.last_change_time:
                query = query.order_by(subquery.c.last_change_time.desc().nulls_last())
            elif filters.filter == ValueFilterType.count_of_changes:
                query = query.order_by(subquery.c.change_count.desc().nulls_last())

            results = await session.execute(query)
            info = []
            for result in results:
                match_id = result[0]
                changes = await ApiOrm.get_ini_last_points(match_id)
                changes_list = [{'type': change[0],
                                 'period': change[1],
                                 'ini_point': change[2],
                                 'last_point': change[3]} for change in changes]

                temp = {
                    'match_id': match_id,
                    'home_id': result[1],
                    'home_name': result[2],
                    'away_id': result[3],
                    'away_name': result[4],
                    'start_time': result[5],
                    'league_name': result[6],
                    'change_count': result[7],
                    'last_change_time': result[8],
                    'changes': changes_list
                }
                info.append(temp)

            return info


async def _dev():
    res = await ApiOrm.get_match_history_by_team_name('Paisas', current_match_id=1598844927)


if __name__ == "__main__":
    asyncio.run(_dev())
