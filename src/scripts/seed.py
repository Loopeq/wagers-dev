import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.db_helper import db_helper
from src.core.models import User
from src.settings import settings
from src.core.utils import get_password_hash
from src.repositories.sport_repository import SportRepository
from src.parser.config import sports


async def seed_first_superuser(session: AsyncSession):
    EMAIL = settings.FIRST_USER_EMAIL
    PASSWORD = get_password_hash(settings.FIRST_USER_PASSWORD)

    stmt = select(User).filter(User.email == EMAIL)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        admin_user = User(
            email=EMAIL,
            password=PASSWORD,
            disabled=False,
            superuser=True,
        )
        session.add(admin_user)

async def seed_sports(session: AsyncSession):
    await SportRepository.create_sports(
        session=session,
        sports=sports,
    )

async def run():
    async with db_helper.session_factory() as session:
        async with session.begin():
            await seed_first_superuser(session=session)
            await seed_sports(session=session)



if __name__ == '__main__':
    asyncio.run(run())
    