import math

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.match_repository import MatchRepository


class RelatedService:
    @staticmethod
    async def get_related(
        session: AsyncSession,
        sport_id: int,
        league_id: int | None = None,
        hours: int | None = None,
        finished: bool = False,
        nulls: bool = False,
        sort_by: str = "team_name",
        sort_order: str = "ASC",
        offset: int = 0,
        limit: int = 20,
    ) -> dict:
        offset = max(offset, 0)
        limit = max(limit, 0)

        match_counts = await MatchRepository.get_related_match_counts(session=session)

        total = await MatchRepository.count_related_matches(
            session=session,
            sport_id=sport_id,
            league_id=league_id,
            hours=hours,
            finished=finished,
            nulls=nulls,
        )

        matches = await MatchRepository.get_related_matches(
            session=session,
            sport_id=sport_id,
            league_id=league_id,
            hours=hours,
            finished=finished,
            nulls=nulls,
            sort_by=sort_by,
            sort_order=sort_order,
            offset=offset,
            limit=limit,
        )

        pages = math.ceil(total / limit) if limit else 1
        current_page = (offset // limit + 1) if limit else 1

        return {
            "matches": matches,
            "match_counts": match_counts,
            "pagination": {
                "pages": pages,
                "current_page": current_page,
                "total": total,
                "offset": offset,
                "limit": limit,
            },
        }
    
    @staticmethod
    async def get_history(
        session: AsyncSession,
        home_id: int,
        away_id: int,
        current_match_id: int,
    ) -> dict:
        home_history = await MatchRepository.get_team_games(
            team_id=home_id,
            current_match_id=current_match_id,
            session=session,
        )

        away_history = await MatchRepository.get_team_games(
            team_id=away_id,
            current_match_id=current_match_id,
            session=session,
        )

        return {
            "home": home_history,
            "away": away_history,
        }