from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.match_repository import MatchRepository
from src.repositories.bet_repository import BetRepository
from src.repositories.archive_repository import ArchiveRepository


class ParserArchiveService:
    @staticmethod
    async def archive_and_clear_matches(
        session: AsyncSession,
        clear_threshold: int = 5,
    ) -> None:
        threshold_time = datetime.utcnow() - timedelta(days=clear_threshold)

        old_matches = await MatchRepository.get_matches_older_than(
            threshold_time=threshold_time,
            session=session,
        )

        if not old_matches:
            return

        old_match_ids = [match.id for match in old_matches]

        await ArchiveRepository.archive_matches(old_matches, session=session)

        old_members = await MatchRepository.get_match_members(
            match_ids=old_match_ids,
            session=session,
        )
        if old_members:
            await ArchiveRepository.archive_match_members(old_members, session=session)

        old_bets = await BetRepository.get_bets_by_match_ids(
            match_ids=old_match_ids,
            session=session,
        )
        if old_bets:
            await ArchiveRepository.archive_bets(old_bets, session=session)

        old_results = await MatchRepository.get_match_results(
            match_ids=old_match_ids,
            session=session,
        )
        if old_results:
            await ArchiveRepository.archive_match_results(old_results, session=session)

        await MatchRepository.delete_matches(old_match_ids, session=session)
        await session.commit()