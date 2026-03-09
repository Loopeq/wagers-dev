from datetime import timedelta
import uuid
from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.core.security import (
    authenticate_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
)
from src.core.utils import get_password_hash
from src.core.schemas import RegisterForm
from src.repositories.invite_repository import InviteRepository
from src.repositories.user_repository import UserRepository


class UserService:

    @staticmethod
    async def login(
        email: str,
        password: str,
        session: AsyncSession,
        response: Response,
    ):
        user = await authenticate_user(email, password, session)

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

    @staticmethod
    async def signup(
        form_data: RegisterForm,
        session: AsyncSession,
        response: Response,
    ):
        invite = await InviteRepository.get_by_code(form_data.invite_code, session)

        if not invite or invite.is_used:
            raise HTTPException(status_code=400, detail="Invalid invite code")

        existing_user = await UserRepository.get_by_email(form_data.email, session)

        if existing_user:
            raise HTTPException(status_code=409, detail="User already exists")

        user = await UserRepository.create(
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

        await InviteRepository.mark_used(invite, user.email, session)

        return user

    @staticmethod
    async def logout(user, session: AsyncSession, response: Response):
        user.session_id = None
        await session.commit()

        response.delete_cookie(
            "access_key",
            secure=True,
            httponly=True,
            samesite="none",
        )

        return {"message": "Logged out successfully"}
