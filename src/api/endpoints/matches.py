from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import CURRENT_ACTIVE_USER
from src.api.schemas import OrderBy
from src.core.crud.api.matches import get_matches as fetch_matches
from src.core.db.db_helper import db_helper

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.get("")
async def get_matches(current_user: CURRENT_ACTIVE_USER,
                      session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
                      sport_id: int,
                      league_id: int | None = None,
                      hours: int | None = None,
                      finished: bool | None = False,
                      nulls: bool | None = False,
                      order_by: OrderBy = OrderBy.start_time):
    matches = await fetch_matches(session=session, sport_id=sport_id, league_id=league_id,
                                  hours=hours, finished=finished, nulls=nulls,
                                  order_by=order_by)
    return matches
