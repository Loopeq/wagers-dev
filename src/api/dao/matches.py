from datetime import datetime, timedelta

from sqlalchemy import func, select, and_
from sqlalchemy.orm import aliased
from sqlalchemy.sql.functions import coalesce

from src.api.schemas import FilterRequest, ValueFilterType
from src.data.database import async_session_factory
from src.data.models import Match, BetChange, League, Bet, MatchMember


def time_filtered(query, filters: FilterRequest, m: Match):
    if (filters.finished is None) and (filters.hour is None):
        query = query.filter(m.start_time >= datetime.utcnow())
    elif filters.finished:
        query = query.filter(m.start_time < datetime.utcnow()).limit(500)
    elif filters.hour:
        query = query.filter(
            and_(m.start_time <= datetime.utcnow() + timedelta(hours=filters.hour),
                 m.start_time >= datetime.utcnow()))
    return query


def value_filtered(query, filters: FilterRequest, subquery, m: Match):
    if filters.filter == ValueFilterType.match_start_time:
        query = query.order_by(m.start_time.asc())
    elif filters.filter == ValueFilterType.last_change_time:
        query = query.order_by(subquery.c.last_change_time.desc().nulls_last())
    elif filters.filter == ValueFilterType.count_of_changes:
        query = query.order_by(subquery.c.change_count.desc().nulls_last())
    return query


class MatchChangeOrm:
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
            query = time_filtered(query, filters, m)
            query = value_filtered(query, filters, subquery, m)
            query = query.group_by(m.id, mm_home.id, mm_home.name, mm_away.id, mm_home.name, m.start_time, le.name,
                                   subquery.c.change_count, subquery.c.last_change_time)

            results = await session.execute(query)
            fields_name = ['match_id', 'home_id', 'home_name', 'away_id', 'away_name', 'start_time', 'league_name',
                           'change_count', 'last_change_time']
            info = [dict(zip(fields_name, result)) for result in results.fetchall()]
            return info
