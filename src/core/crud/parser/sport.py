from sqlalchemy.exc import IntegrityError

from src.core.db.db_helper import db_helper
from src.core.models import Sport


async def add_sports(sports: dict):
    async with db_helper.session_factory() as session:
        for name in sports.keys():
            try:
                session.add(Sport(id=sports[name], name=name))
                await session.commit()
            except Exception:
                await session.rollback()
