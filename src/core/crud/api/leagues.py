from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import League


async def get_leagues(session: AsyncSession, sport_id: int):
    result = await session.execute(select(League).filter(League.sport_id == sport_id))
    leagues = result.scalars()
    return leagues
