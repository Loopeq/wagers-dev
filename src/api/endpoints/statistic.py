from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies import CURRENT_ACTIVE_USER
from src.core.crud.api.straight import get_team_games
from src.core.db.db_helper import db_helper

router = APIRouter(prefix="/statistic", tags=["Statistic"])


@router.get("/history")
async def get_history(
    current_user: CURRENT_ACTIVE_USER,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    home_id: int,
    away_id: int,
    current_match_id: int,
):
    home_history = await get_team_games(
        team_id=home_id, current_match_id=current_match_id, session=session
    )
    away_history = await get_team_games(
        team_id=away_id, current_match_id=current_match_id, session=session
    )

    return {"home": home_history, "away": away_history}
