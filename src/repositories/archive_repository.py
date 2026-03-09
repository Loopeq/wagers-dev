from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import (
    MatchArchive,
    MatchMemberArchive,
    MatchResultArchive,
    BetArchive,
)
from src.core.utils import to_dict_for_insert
from src.core.crud.parser.bet import bulk_insert


class ArchiveRepository:
    @staticmethod
    async def archive_matches(matches: list, session: AsyncSession) -> None:
        await session.execute(
            insert(MatchArchive).values([to_dict_for_insert(match) for match in matches])
        )
        await session.flush()

    @staticmethod
    async def archive_match_members(members: list, session: AsyncSession) -> None:
        await session.execute(
            insert(MatchMemberArchive).values(
                [to_dict_for_insert(member) for member in members]
            )
        )

    @staticmethod
    async def archive_match_results(results: list, session: AsyncSession) -> None:
        await session.execute(
            insert(MatchResultArchive).values(
                [to_dict_for_insert(result) for result in results]
            )
        )

    @staticmethod
    async def archive_bets(bets: list, session: AsyncSession) -> None:
        await bulk_insert(session, BetArchive, bets)