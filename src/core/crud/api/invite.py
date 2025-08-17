import stat
from fastapi import HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.utils import generate_invite_code
from src.core.models import InviteCode

class InviteCodeOrm:

    @staticmethod
    async def release_code(session: AsyncSession) -> InviteCode:
        code = InviteCode(
            code=generate_invite_code(),
            is_used=False, 
        )
        session.add(code)
        await session.commit()
        await session.refresh(code)
        return code


    @staticmethod
    async def get_by_code(code: str, session: AsyncSession) -> InviteCode | None:
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
        stmt = (
            select(InviteCode).order_by(InviteCode.created_at.desc())
        )
        try:
            result = await session.execute(stmt)
            return result.scalars()
        except Exception:
            raise HTTPException(
                status_code=stat.HTTP_400_BAD_REQUEST,
                detail="Could not get codes"
            )
    
    @staticmethod
    async def remove_code(code: str, session: AsyncSession):
        stmt = (
            delete(InviteCode)
            .where(InviteCode.code == code, InviteCode.is_used == False)
            .returning(InviteCode.code) 
        )
        try:
            result = await session.execute(stmt)
            deleted_code = result.scalar()  
            await session.commit()

            if not deleted_code:
                raise HTTPException(
                    status_code=stat.HTTP_404_NOT_FOUND,
                    detail="Code not found or already used"
                )

            return {"removed_code": deleted_code}

        except Exception:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not remove code"
            )