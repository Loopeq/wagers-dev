from typing import Annotated, List
from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession
from src.core.db.db_helper import db_helper
from src.api.dependencies import CURRENT_ADMIN_USER
from src.core.crud.api.invite import InviteCodeOrm
from src.core.schemas import InviteCode, UserOutAdmin
from src.core.crud.api.user import UserOrm

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/release_code")
async def release_invite_code(
    admin_user: CURRENT_ADMIN_USER,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],

):
    code = await InviteCodeOrm.release_code(session=session) 
    return code

@router.get("/users", response_model=List[UserOutAdmin])
async def get_users(
    admin_user: CURRENT_ADMIN_USER,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> List[UserOutAdmin]: 
    response = await UserOrm.get_users(session=session)
    return response


@router.get("/codes", response_model=List[InviteCode])
async def get_users(
    admin_user: CURRENT_ADMIN_USER,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
) -> List[InviteCode]: 
    response = await InviteCodeOrm.get_codes(session=session)
    return response

@router.delete("/code")
async def remove_code(
    admin_user: CURRENT_ADMIN_USER,
    code: str,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
): 
    response = await InviteCodeOrm.remove_code(code=code, session=session)
    return response
