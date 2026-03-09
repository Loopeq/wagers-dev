from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.models import User


class UserRepository:

    @staticmethod
    async def get_by_email(email: str, session: AsyncSession):
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_telegram_id(tg_id: str, session: AsyncSession):
        stmt = select(User).where(User.telegram_id == tg_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(email: str, password: str, session: AsyncSession):
        user = User(email=email, password=password)

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return user

    @staticmethod
    async def get_users(session: AsyncSession):
        stmt = select(User)
        result = await session.execute(stmt)
        return result.scalars().all()
