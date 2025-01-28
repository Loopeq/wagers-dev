from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from starlette import status

from src.core.models import User


class UserOrm:
    @staticmethod
    async def get_user_by_uuid(
            uuid: uuid.UUID, session: AsyncSession
    ) -> User | None:
        stmt = select(User).filter(User.uuid == uuid)
        try:
            user = await session.execute(stmt)
            return user.scalar_one_or_none()
        except:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )