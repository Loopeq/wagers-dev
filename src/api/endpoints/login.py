from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from src.api.dependencies import CURRENT_ACTIVE_USER
from src.core.schemas import Token, UserOut
from src.core.security import (
    authenticate_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
)
from src.core.db.db_helper import db_helper
import uuid

router = APIRouter(prefix="/login", tags=["Login"])


@router.post("", response_model=UserOut)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    response: Response
):
    user = await authenticate_user(
        form_data.username, form_data.password, session
    )
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
        data={"sub": str(user.email), "sid": session_id}, expires_delta=access_token_expires
    )

    response.set_cookie(
        key='access_key',
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return user


@router.get("/check")
async def check(current_user: CURRENT_ACTIVE_USER):
    return current_user
