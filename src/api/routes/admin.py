from typing import Annotated, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import CURRENT_ADMIN_USER
from src.core.db.db_helper import db_helper
from src.core.schemas import InviteCode, UserOutAdmin
from src.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/release_code")
async def release_invite_code(
    admin_user: CURRENT_ADMIN_USER,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    return await AdminService.release_invite_code(session)


@router.get("/users", response_model=List[UserOutAdmin])
async def get_users(
    admin_user: CURRENT_ADMIN_USER,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    return await AdminService.get_users(session)


@router.get("/codes", response_model=List[InviteCode])
async def get_codes(
    admin_user: CURRENT_ADMIN_USER,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    return await AdminService.get_codes(session)


@router.delete("/code")
async def remove_code(
    admin_user: CURRENT_ADMIN_USER,
    code: str,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    return await AdminService.remove_code(code, session)
