from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import CURRENT_ACTIVE_USER
from src.core.crud.api.base import get_leagues as fetch_leagues
from src.core.db.db_helper import db_helper
from src.core.schemas import LeagueDTO

router = APIRouter(prefix="/leagues", tags=["Leagues"])


@router.get("", response_model=list[LeagueDTO])
async def get_leagues(current_user: CURRENT_ACTIVE_USER,
                      session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
                      sport_id: int):
    leagues = await fetch_leagues(session=session, sport_id=sport_id)
    return leagues

