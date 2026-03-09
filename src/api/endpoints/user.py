from datetime import timedelta
import uuid
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from src.core.db.db_helper import db_helper
from src.core.crud.api.user import UserOrm
from src.core.security import (
    authenticate_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
)
from starlette import status
from src.core.utils import get_password_hash
from src.core.schemas import RegisterForm
from src.core.crud.api.invite import InviteCodeOrm
from src.api.dependencies import CURRENT_ACTIVE_USER
from src.core.schemas import UserOut

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
    user = await authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    session_id = str(uuid.uuid4())
    user.session_id = session_id
    await session.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.email), "sid": session_id},
        expires_delta=access_token_expires,
    )

    response.set_cookie(
        key="access_key",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return user


@router.post("/signup", response_model=UserOut)
async def signup(
    form_data: RegisterForm,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    response: Response,
):
    invite = await InviteCodeOrm.get_by_code(form_data.invite_code, session)
    if not invite or invite.is_used:
        raise HTTPException(status_code=400, detail="Invalid invite code")

    existing_user = await UserOrm.get_user_by_email(form_data.email, session)
    if existing_user:
        raise HTTPException(status_code=409, detail="User already exists")

    user = await UserOrm.create_user(
        email=form_data.email,
        password=get_password_hash(form_data.password),
        session=session,
    )

    session_id = str(uuid.uuid4())
    user.session_id = session_id
    await session.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.email), "sid": session_id},
        expires_delta=access_token_expires,
    )

    response.set_cookie(
        key="access_key",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    await InviteCodeOrm.mark_used(invite, user.email, session)

    return user


@router.post("/logout")
async def logout(
    current_user: CURRENT_ACTIVE_USER,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    response: Response,
):
    current_user.session_id = None
    await session.commit()

    response.delete_cookie("access_key", secure=True, httponly=True, samesite="none")

    return {"message": "Logged out successfully"}
