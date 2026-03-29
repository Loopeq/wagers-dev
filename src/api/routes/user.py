from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import CURRENT_ACTIVE_USER
from src.core.db.db_helper import db_helper
from src.core.schemas import RegisterForm, UserOut
from src.services.user_service import UserService

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: CURRENT_ACTIVE_USER):
    return current_user


@router.post("/login", response_model=UserOut)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    response: Response,
):
    return await UserService.login(
        form_data.username,
        form_data.password,
        session,
        response,
    )


@router.post("/signup", response_model=UserOut)
async def signup(
    form_data: RegisterForm,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    response: Response,
):
    return await UserService.signup(form_data, session, response)


@router.post("/logout")
async def logout(
    current_user: CURRENT_ACTIVE_USER,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    response: Response,
):
    return await UserService.logout(current_user, session, response)
