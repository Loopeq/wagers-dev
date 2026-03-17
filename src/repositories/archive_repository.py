from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import (
    MatchArchive,
    MatchMemberArchive,
    MatchResultArchive,
    BetArchive,
)
from src.core.utils import to_dict_for_insert


class ArchiveRepository:

    @staticmethod
    async def _bulk_insert(model, objects, session: AsyncSession):
        BATCH_SIZE = 1000
        for i in range(0, len(objects), BATCH_SIZE):
            chunk = objects[i : i + BATCH_SIZE]
            await session.execute(
                insert(model).values([to_dict_for_insert(obj) for obj in chunk]).on_conflict_do_nothing()
            )
            
    @staticmethod
    async def archive_matches(matches: list, session: AsyncSession) -> None:
        await session.execute(
            insert(MatchArchive).values([to_dict_for_insert(match) for match in matches]).on_conflict_do_nothing()
        )
        await session.flush()

    @staticmethod
    async def archive_match_members(members: list, session: AsyncSession) -> None:
        await session.execute(
            insert(MatchMemberArchive).values(
                [to_dict_for_insert(member) for member in members]
            ).on_conflict_do_nothing()
        )

    @staticmethod
    async def archive_match_results(results: list, session: AsyncSession) -> None:
        await session.execute(
            insert(MatchResultArchive).values(
                [to_dict_for_insert(result) for result in results]
            ).on_conflict_do_nothing()
        )

    @staticmethod
    async def archive_bets(bets: list, session: AsyncSession) -> None:
        await ArchiveRepository._bulk_insert(session, BetArchive, bets).on_conflict_do_nothing()