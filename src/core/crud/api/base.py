from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from src.core.models import Sport, League, Match


async def get_sports(session: AsyncSession):
    stmt = (
        select(Sport.id, Sport.name, func.count(Match.id).label("match_count"))
        .outerjoin(League, League.sport_id == Sport.id)
        .outerjoin(Match, Match.league_id == League.id)
        .where(Match.start_time > datetime.utcnow())
        .group_by(Sport.id, Sport.name)
    )

    result = await session.execute(stmt)
    return [{"id": r[0], "name": r[1], "match_count": r[2]} for r in result]


async def get_leagues(session: AsyncSession, sport_id: int):
    result = await session.execute(select(League).filter(League.sport_id == sport_id))
    leagues = result.scalars()
    return leagues
