from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import CURRENT_ACTIVE_USER
from src.core.db.db_helper import db_helper

router = APIRouter(prefix="/history", tags=["History"])


@router.get("")
async def get_team_history(team_name: str,
                           current_match_id: int,
                           league_id: int,
                           current_user: CURRENT_ACTIVE_USER,
                           session: Annotated[AsyncSession, Depends(db_helper.session_getter)]):
    return '123'
