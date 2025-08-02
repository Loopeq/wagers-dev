import math
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies import CURRENT_ACTIVE_USER
from src.core.crud.api.related import get_matches as fetch_matches, get_upcoming_match_counts_by_sport
from src.core.db.db_helper import db_helper

router = APIRouter(prefix="/related", tags=["Related"])


@router.get("")
async def get_related(current_user: CURRENT_ACTIVE_USER,
                      session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
                      sport_id: int,
                      league_id: int | None = None,
                      hours: int | None = None,
                      finished: bool | None = False,
                      nulls: bool | None = False,
                      sort_by: str | None = "team_name",
                      sort_order: str | None = "ASC",
                      offset: int | None = None,
                      limit: int | None = None):
    match_counts = await get_upcoming_match_counts_by_sport(session=session)
    matches = await fetch_matches(session=session, sport_id=sport_id, league_id=league_id,
                                  hours=hours, finished=finished, nulls=nulls,
                                  sort_by=sort_by, sort_order=sort_order)
    pagination = {
        'pages': math.ceil(len(matches) / limit),
        'current_page': offset // limit + 1
    }
    return {"matches": matches[offset: offset + limit], "match_counts": match_counts, "pagination": pagination}
