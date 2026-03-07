from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies import CURRENT_ACTIVE_USER
from src.core.crud.api.base import get_sports as fetch_sports
from src.core.db.db_helper import db_helper
from src.core.schemas import SportDTO
from src.parser.config import sports_ru

router = APIRouter(prefix="/sports", tags=["Sports"])


@router.get("", response_model=list[SportDTO])
async def get_sports(
    current_user: CURRENT_ACTIVE_USER,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    sports = await fetch_sports(session=session)
    sports = [{**sport, "name_ru": sports_ru[sport["name"]]} for sport in sports]
    return sports
