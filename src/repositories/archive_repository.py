from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.logger import get_module_logger
from src.core.models import (
    MatchArchive,
    MatchMemberArchive,
    MatchResultArchive,
    BetArchive,
)
from src.core.utils import to_dict_for_insert

logger = get_module_logger(__name__)

class ArchiveRepository:

    @staticmethod
    async def _bulk_insert(session: AsyncSession, model, objects: list) -> None:
        if not objects:
            return
            
        BATCH_SIZE = 1000
        for i in range(0, len(objects), BATCH_SIZE):
            chunk = objects[i : i + BATCH_SIZE]
            try:
                await session.execute(
                    insert(model)
                    .values([to_dict_for_insert(obj) for obj in chunk])
                    .on_conflict_do_nothing()
                )
            except:
                logger.error('Exception while archive events')

    @staticmethod
    async def archive_matches(matches: list, session: AsyncSession) -> None:
        if not matches:
            return
        await ArchiveRepository._bulk_insert(session, MatchArchive, matches)

    @staticmethod
    async def archive_match_members(members: list, session: AsyncSession) -> None:
        if not members:
            return
        await ArchiveRepository._bulk_insert(session, MatchMemberArchive, members)

    @staticmethod
    async def archive_match_results(results: list, session: AsyncSession) -> None:
        if not results:
            return
        await ArchiveRepository._bulk_insert(session, MatchResultArchive, results)

    @staticmethod
    async def archive_bets(bets: list, session: AsyncSession) -> None:
        if not bets:
            return
        await ArchiveRepository._bulk_insert(session, BetArchive, bets)