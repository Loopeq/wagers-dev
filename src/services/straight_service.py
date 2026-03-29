from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.builders.straight_builder import StraightBuilder
from src.repositories.bet_repository import BetRepository
from src.repositories.match_repository import MatchRepository


class StraightService:
    @staticmethod
    async def load_straight(match_id: int, child_id: int | None, session: AsyncSession):
        match = await MatchRepository.get_match_with_teams(match_id, session)
        if not match:
            raise HTTPException(404, "Not found")

        builder = StraightBuilder(
            match_id=match_id,
            child_id=child_id,
            sport_id=match["match"]["sport_id"],
        )

        changes = await BetRepository.get_changes(
            match_ids=[match_id, child_id],
            periods=[],
            session=session,
        )
        comparison = await BetRepository.get_initial_last_points(
            match_id=match_id,
            child_id=child_id,
            session=session,
        )

        mapped_changes, periods = builder.map_changes(changes)
        mapped_comparison = builder.map_comparison(comparison)

        return {
            **match,
            "changes": mapped_changes,
            "comparison": mapped_comparison,
            "periods": periods,
        }
