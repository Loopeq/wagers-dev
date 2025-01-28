from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Bet


async def get_count_of_changes(match_id: int, session: AsyncSession):
    result = await session.execute(select(func.count(Bet)).filter(Bet.match_id == match_id,
                                                                  Bet.version > 1))
    return result.one()


async def get_changes(match_id: int):
    pass