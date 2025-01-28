import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.db_helper import db_helper
from src.core.models import User
from src.core.settings import settings
from src.core.utils import get_password_hash


async def create_first_superuser(session: AsyncSession):
    UUID = settings.FIRST_USER_UUID
    PASSWORD = get_password_hash(settings.FIRST_USER_PASSWORD)

    stmt = select(User).filter(User.uuid == UUID)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        admin_user = User(
            uuid=UUID,
            password=PASSWORD,
            disabled=False,
            superuser=True,
        )
        session.add(admin_user)
        await session.commit()


async def main():
    async with db_helper.session_factory() as session:
        await create_first_superuser(session)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
