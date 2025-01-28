from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from src.core.models import User


class UserOrm:
    @staticmethod
    async def get_user_by_uuid(
            uuid: uuid.UUID, session: AsyncSession
    ) -> User | None:
        stmt = select(User).filter(User.uuid == uuid)
        user = await session.execute(stmt)
        return user.scalar_one_or_none()
