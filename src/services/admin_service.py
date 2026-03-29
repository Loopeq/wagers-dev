from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.core.models import InviteCode
from src.core.utils import generate_invite_code
from src.repositories.invite_repository import InviteRepository
from src.repositories.user_repository import UserRepository


class AdminService:

    @staticmethod
    async def release_invite_code(session: AsyncSession):
        invite = InviteCode(
            code=generate_invite_code(),
            is_used=False,
        )

        return await InviteRepository.create(invite, session)

    @staticmethod
    async def get_users(session: AsyncSession):
        return await UserRepository.get_users(session)

    @staticmethod
    async def get_codes(session: AsyncSession):
        return await InviteRepository.get_codes(session)

    @staticmethod
    async def remove_code(code: str, session: AsyncSession):
        deleted_code = await InviteRepository.remove_code(code, session)

        if not deleted_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Code not found or already used",
            )

        return {"removed_code": deleted_code}
