from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Sport

class SportRepository:

    @staticmethod
    async def create_sports(session: AsyncSession, sports: dict[str, int], sports_ru: dict[str, str]) -> None:
        if not sports:
            return

        values = []
        for sport_key, sport_id in sports.items():
            sport_name = sports_ru.get(sport_key, sport_key)
            values.append(
                {
                    "id": sport_id,
                    "name": sport_name,
                }
            )

        await session.execute(
            insert(Sport)
            .values(values)
            .on_conflict_do_nothing(index_elements=["id"])
        )