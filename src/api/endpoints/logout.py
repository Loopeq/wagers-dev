from typing import Annotated
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies import CURRENT_ACTIVE_USER
from src.core.db.db_helper import db_helper

router = APIRouter(prefix="/logout", tags=["Logout"])


@router.post("/")
async def logout(
    current_user: CURRENT_ACTIVE_USER,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    response: Response
):
    current_user.session_id = None
    await session.commit()

    response.delete_cookie("access_key", secure=True, httponly=True, samesite="none")

    return {"message": "Logged out successfully"}