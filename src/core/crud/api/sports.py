import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Sport


async def get_sports(session: AsyncSession):
    result = await session.execute(select(Sport))
    sports = result.scalars()
    return sports
