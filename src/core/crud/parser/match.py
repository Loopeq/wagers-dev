import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from src.core.db.db_helper import db_helper
from src.core.models import Match, League, MatchMember
from src.core.schemas import MatchUpcomingDTO


async def check_exist(id: int):
    async with db_helper.session_factory() as session:
        query = select(Match.id).filter(Match.id == id)
        result = await session.execute(query)
        return result.one_or_none()


async def add_match_cascade(league: League, match: Match, match_member_home: MatchMember,
                            match_member_away: MatchMember):
    async with db_helper.session_factory() as session:
        async with session.begin():
            try:
                await session.execute(insert(League).values(
                    id=league.id,
                    sport_id=league.sport_id,
                    name=league.name).on_conflict_do_nothing())
                await session.execute(
                    insert(Match).values(
                        id=match.id,
                        league_id=match.league_id,
                        start_time=match.start_time).on_conflict_do_nothing())
                await session.execute(insert(MatchMember).values(
                    match_id=match_member_home.match_id,
                    name=match_member_home.name,
                    status=match_member_home.status,
                    side=match_member_home.side).on_conflict_do_nothing())
                await session.execute(insert(MatchMember).values(
                    match_id=match_member_away.match_id,
                    name=match_member_away.name,
                    status=match_member_away.status,
                    side=match_member_away.side).on_conflict_do_nothing())
            except:
                logging.error(f'Error while add header for Match: {match.to_dict()}. League: {league.to_dict()}')


async def get_upcoming_matches(start_timedelta: timedelta,
                               end_timedelta: timedelta | None):
    async with db_helper.session_factory() as session:
        current_time = datetime.utcnow()
        query = select(Match.start_time, Match.id)
        query = query.filter(Match.start_time > current_time)

        if start_timedelta:
            query = query.filter(Match.start_time > current_time + start_timedelta)

        if end_timedelta:
            query = query.filter(Match.start_time <= current_time + end_timedelta)

        result = await session.execute(query)
        matches = result.fetchall()
        matches_dto = [MatchUpcomingDTO.model_validate(row, from_attributes=True) for row in matches]
        return matches_dto
