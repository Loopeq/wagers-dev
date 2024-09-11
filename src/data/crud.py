from sqlalchemy import Integer, and_, cast, func, insert, inspect, or_, select, text
from sqlalchemy.orm import aliased, contains_eager, joinedload, selectinload
from src.data.models import Sport, League, Match, MatchMember, MatchResultEnum, MatchSideEnum, BetTypeEnum, Bet, BetValue
from src.data.database import Base, async_engine, async_session_factory


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


class MatchOrm:

    @staticmethod
    async def insert_match():
        pass
