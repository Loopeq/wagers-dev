import asyncio

from sqlalchemy import select, text

from src.data.database import async_session_factory
from src.data.models import Match, Bet
import json


class ApiOrm:
    @staticmethod
    async def get_point_changes():
        async with async_session_factory() as session:
            stmt = text('''
                    SELECT 
                    m.id as match_id,
                    b_old.point as old_point, b_new.point as new_point, 
                    b_new.period, 
                    b_new.type,
                    m.start_time,
                    b_new.created_at,
                    mm_home.name as home_name,
                    mm_home.id as home_id,
                    mm_away.name as away_name,
                    mm_away.id as away_id,
                    l.name
                    FROM bet_change as bc 
                    LEFT JOIN bet b_old ON bc.old_bet_id = b_old.id
                    LEFT JOIN bet b_new ON bc.new_bet_id = b_new.id
                    LEFT JOIN match m ON b_new.match_id = m.id 
                    LEFT JOIN match_member mm_home 
                    ON mm_home.match_id = m.id AND mm_home.side = 'home'
                    LEFT JOIN match_member mm_away
                    ON mm_away.match_id = m.id AND mm_away.side = 'away'
                    LEFT JOIN league l ON l.id = m.league_id
                    ''')
            result = await session.execute(stmt)
            return result


async def _dev():
    await ApiOrm.get_point_changes()


if __name__ == "__main__":
    asyncio.run(_dev())
