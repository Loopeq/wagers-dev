import asyncio
import datetime
from datetime import timedelta
from typing import Optional, List

from sqlalchemy import select, text, func, literal_column
from sqlalchemy.orm import aliased
from sqlalchemy.sql.functions import coalesce
from sqlalchemy.sql.operators import and_

from src.api.schemas import FilterRequest, ValueFilterType
from src.data.database import async_session_factory
from src.data.models import Match, Bet, BetChange, League, MatchMember
import json


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
                    .filter(m.id == match_id[0])
                result = await session.execute(query)
                info = result.fetchone()
                info = {'match_id': info[0], 'home_name': info[1], 'away_name': info[2], 'start_time': info[3]}
                history.append(info)
            return history

    @staticmethod
    async def get_point_change(match_id: int):
        async with async_session_factory() as session:
            bc = aliased(BetChange)
            old_b = aliased(Bet)
            new_b = aliased(Bet)
            query = select(old_b.home_cf,
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

            results = await session.execute(query)
            result = [{'old_home_cf': result[0],
                       'new_home_cf': result[1],
                       'old_away_cf': result[2],
                       'new_away_cf': result[3],
                       'old_point': result[4],
                       'new_point': result[5],
                       'type': result[6],
                       'period': result[7],
                       'created_at': result[8]} for result in results.fetchall()]

            return result

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
                query = query.filter(m.start_time < datetime.datetime.utcnow())
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
            results = [{
                'match_id': result[0],
                'home_id': result[1],
                'home_name': result[2],
                'away_id': result[3],
                'away_name': result[4],
                'start_time': result[5],
                'league_name': result[6],
                'change_count': result[7],
                'last_change_time': result[8],
            } for result in results]

            return results


async def _dev():
    res = await ApiOrm.get_match_history_by_team_name('Kepler', 123)
    print(res)


if __name__ == "__main__":
    asyncio.run(_dev())
