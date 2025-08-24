from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies import CURRENT_ACTIVE_USER
from src.core.db.db_helper import db_helper
from src.api.repositories.straight import get_straight, get_straight_full_history

router = APIRouter(prefix="/straight", tags=["Straight"])


class Period(BaseModel):
    type: str
    period: int



@router.get("")
async def get_straight_changes(
        current_user: CURRENT_ACTIVE_USER,
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        match_id: int,
        child_id: int | None = None,
):
    straight = await get_straight(match_id=match_id, child_id=child_id, session=session)
    return straight


@router.get("/full")
async def get_straight_full_changes(
        current_user: CURRENT_ACTIVE_USER,
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        match_id: int,
        child_id: int | None = None,
):
    straight_full = await get_straight_full_history(match_id=match_id, child_id=child_id, session=session)
    return straight_full
