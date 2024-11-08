import asyncio
from datetime import datetime

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import aliased

from src.data.crud import MatchOrm
from src.logs import logger
from src.parser.calls.league import fetch
from src.data.database import async_session_factory
from src.data.models import MatchMember, Match, MatchResult
from src.parser.calls.event_details import get_match_details



class HistoryOrm:

    @staticmethod
    async def get_match_history_by_team_name(team_name: str, current_match_id: int, league_id: int):
        async with async_session_factory() as session:
            mm_home = aliased(MatchMember)
            mm_away = aliased(MatchMember)
            m = aliased(Match)
            ms = aliased(MatchResult)

            query = select(
                m.id,
                mm_home.name.label("home_name"),
                mm_away.name.label("away_name"),
                m.start_time,
                m.league_id,
                ms.team_1_score.label('team_1_score'),
                ms.team_2_score.label('team_2_score'),
            ).select_from(m) \
                .join(mm_home, and_(mm_home.match_id == m.id, mm_home.side == 'home')) \
                .join(mm_away, and_(mm_away.match_id == m.id, mm_away.side == 'away')) \
                .join(ms, and_(ms.match_id == m.id, ms.period == 0)) \
                .filter(
                    or_(mm_home.name == team_name, mm_away.name == team_name),
                    m.id != current_match_id,
                    m.start_time < datetime.utcnow(),
                    m.league_id == league_id,
            ).order_by(m.start_time.desc())

            result = await session.execute(query)

            history = [{
                'match_id': row.id,
                'home_name': row.home_name,
                'away_name': row.away_name,
                'start_time': row.start_time,
                'details': {
                    'team_1_score': row.team_1_score,
                    'team_2_score': row.team_2_score
                }
            } for row in result.fetchall()]

            return history


async def _dev():
    await get_history_details()

if __name__ == "__main__":
    asyncio.run(_dev())
