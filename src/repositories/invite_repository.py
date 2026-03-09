from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.models import InviteCode


class InviteRepository:

    @staticmethod
    async def create(code: InviteCode, session: AsyncSession):
        session.add(code)
        await session.commit()
        await session.refresh(code)
        return code

    @staticmethod
    async def get_by_code(code: str, session: AsyncSession):
        stmt = select(InviteCode).where(InviteCode.code == code)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def mark_used(invite: InviteCode, user_email: str, session: AsyncSession):
        stmt = (
            update(InviteCode)
            .where(InviteCode.id == invite.id)
            .values(is_used=True, user_email=user_email)
            .execution_options(synchronize_session="fetch")
        )
        await session.execute(stmt)
        await session.commit()

    @staticmethod
    async def get_codes(session: AsyncSession):
        stmt = select(InviteCode).order_by(InviteCode.created_at.desc())
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def remove_code(code: str, session: AsyncSession):
        stmt = (
            delete(InviteCode)
            .where(InviteCode.code == code, InviteCode.is_used == False)
            .returning(InviteCode.code)
        )

        result = await session.execute(stmt)
        deleted_code = result.scalar()

        if not deleted_code:
            return None

        await session.commit()
        return deleted_code
