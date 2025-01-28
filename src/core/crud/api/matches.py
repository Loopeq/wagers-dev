from datetime import datetime, timedelta

from sqlalchemy import select, func, case, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import OrderBy
from src.core.models import Match, League, Bet


async def get_matches(session: AsyncSession,
                      sport_id: int,
                      league_id: int | None,
                      hours: int | None,
                      nulls: bool | None,
                      finished: bool | None,
                      order_by: OrderBy | None
                      ):
    count_case = func.count(case((Bet.version > 1, Bet.id), else_=None))
    last_update = func.max(Bet.created_at)
    query = select(Match.id, Match.start_time,
                   Match.league_id,
                   count_case.label('change_count'),
                   last_update.label('last_update')) \
        .join(League, League.id == Match.league_id) \
        .join(Bet, Bet.match_id == Match.id) \
        .filter(League.sport_id == sport_id) \
        .group_by(Match.id, Match.start_time, Match.league_id)

    if league_id:
        query = query.filter(League.id == league_id)
    if not finished and finished is not None:
        query = query.filter(Match.start_time >= datetime.utcnow())
    if not nulls and nulls is not None:
        query = query.having(count_case > 0)
    if hours:
        query = query.filter(Match.start_time >= datetime.utcnow() + timedelta(hours=hours))

    match order_by:
        case order_by.start_time:
            query = query.order_by(asc(order_by.value))
        case order_by.change_count | order_by.last_update:
            query = query.order_by(desc(order_by.value))

    result = await session.execute(query)
    results = result.fetchall()
    matches = [
        {'id': result[0],
         'start_time': result[1],
         'league_id': result[2],
         'change_count': result[3]}
        for result in results]

    return matches
