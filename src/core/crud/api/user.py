from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from starlette import status

from src.core.models import User


class UserOrm:

    @staticmethod
    async def get_user_by_email(
            email: str, session: AsyncSession
    ) -> User | None:
        stmt = select(User).filter(User.email == email)
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
        )

    @staticmethod
    async def get_user_by_telegram_id(
            tg_id: str, session: AsyncSession
    ) -> User | None:
        stmt = select(User).filter(User.telegram_id == tg_id)
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect tg_id",
        )


    @staticmethod
    async def create_user(
        email: str, password: str, session: AsyncSession 
    ) -> User:
        new_user = User(email=email, password=password)
        session.add(new_user)

        try:
            await session.commit()
            await session.refresh(new_user)
            return new_user
        except:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create user"
            )
    
    @staticmethod
    async def get_users(session: AsyncSession):
        stmt = (
            select(User)
        )
        try:
            result = await session.execute(stmt)
            return result.scalars()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not get users"
            )
    