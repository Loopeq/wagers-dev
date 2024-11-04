from datetime import datetime

from cachetools import TTLCache
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.parser.calls.league import fetch
from src.data.database import async_session_factory
from src.data.models import MatchMember, Match, League, MatchResult
from src.parser.calls.event_details import get_match_details


class LeagueManager:
    cache = TTLCache(maxsize=128, ttl=43200)

    @staticmethod
    async def is_right_order(league_id):

        if league_id in LeagueManager.cache:
            return LeagueManager.cache[league_id]
        else:
            leagues = await fetch()
            if not leagues:
                return None

            for league in leagues:
                if league['id'] == league_id:
                    order = league['homeTeamType'] == 'Team1'
                    LeagueManager.cache[league_id] = order
                    return order
            return None


async def get_history_details(session: AsyncSession, row) -> dict | None:
    details = None
    details_stmt = select(MatchResult).filter(MatchResult.match_id == row.id, MatchResult.period == 0)
    details_result = await session.execute(details_stmt)
    details_data = details_result.fetchone()

    if details_data:
        details_data = details_data[0]
        details = {
            'period': details_data.period,
            'team_1_score': details_data.team_1_score,
            'team_2_score': details_data.team_2_score
        }
        return details

    order = await LeagueManager.is_right_order(row.league_id)
    api_data = await get_match_details(row.id)
    if not api_data:
        return

    for value in api_data:
        if value['number'] == 0 and order is not None:
            team_1_score = value['team_1_score'] if order else value['team_2_score']
            team_2_score = value['team_2_score'] if order else value['team_1_score']
            new_res = MatchResult(
                match_id=row.id,
                period=value['number'],
                team_1_score=team_1_score,
                team_2_score=team_2_score
            )
            session.add(new_res)
            await session.commit()
            details = {
                'period': value['number'],
                'team_1_score': team_1_score,
                'team_2_score': team_2_score,
            }

    return details


class HistoryOrm:

    @staticmethod
    async def get_match_history_by_team_name(team_name: str, current_match_id: int, league_id: int):
        async with async_session_factory() as session:
            mm_home = aliased(MatchMember)
            mm_away = aliased(MatchMember)
            m = aliased(Match)

            query = select(
                m.id,
                mm_home.name.label("home_name"),
                mm_away.name.label("away_name"),
                m.start_time,
            ).select_from(m) \
                .join(mm_home, and_(mm_home.match_id == m.id, mm_home.side == 'home')) \
                .join(mm_away, and_(mm_away.match_id == m.id, mm_away.side == 'away')) \
                .filter(
                    or_(mm_home.name == team_name, mm_away.name == team_name),
                    m.id != current_match_id,
                    m.start_time < datetime.utcnow(),
                    m.league_id == league_id,
            ).order_by(m.start_time.desc())

            result = await session.execute(query)
            history = []
            for row in result.fetchall():
                details = await get_history_details(session, row)
                history.append({
                    'match_id': row.id,
                    'home_name': row.home_name,
                    'away_name': row.away_name,
                    'start_time': row.start_time,
                    'details': details
                })
            return history
