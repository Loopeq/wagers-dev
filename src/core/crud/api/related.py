from datetime import datetime, timedelta

from sqlalchemy import select, func, case, asc, desc, distinct, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.core.models import Match, League, Bet, MatchMember, Team


async def get_upcoming_match_counts_by_sport(session: AsyncSession):
    utc_now = datetime.utcnow()
    bet_match = aliased(Match)
    bet = aliased(Bet)

    query = select(
        League.sport_id,
        func.count(distinct(Match.id)).label("upcoming_matches_with_changes")
    ).outerjoin(Match, League.id == Match.league_id) \
        .outerjoin(bet_match, or_(bet_match.id == Match.id, bet_match.parent_id == Match.id)) \
        .outerjoin(bet, bet.match_id == bet_match.id) \
        .filter(
        Match.start_time > utc_now,
        Match.parent_id.is_(None),
        bet.version >= 1
    ) \
        .group_by(League.sport_id)

    result = await session.execute(query)
    result = result.fetchall()
    return [{'sport_id': row[0], 'count': row[1]} for row in result]


async def get_matches(session: AsyncSession,
                      sport_id: int,
                      league_id: int | None,
                      hours: int | None,
                      nulls: bool | None,
                      finished: bool | None,
                      sort_by: str | None,
                      sort_order: str | None,
                      ):
    utc_now = datetime.utcnow()
    home_team = aliased(Team)
    away_team = aliased(Team)
    child_match = aliased(Match)
    bet_match = aliased(Match)
    bet = aliased(Bet)
    count_case = func.count(case((bet.version >= 1, bet.id), else_=None))
    last_update = func.max(bet.created_at).filter(bet.version >= 1)
    query = select(Match.id, Match.start_time,
                   League.name,
                   count_case.label('change_count'),
                   last_update.label('last_update'),
                   home_team.name.label('home_name'),
                   away_team.name.label('away_name'),
                   home_team.id.label('home_team_id'),
                   away_team.id.label('away_team_id'),
                   Match.created_at,
                   child_match.id) \
        .outerjoin(League, League.id == Match.league_id) \
        .outerjoin(MatchMember, MatchMember.match_id == Match.id) \
        .outerjoin(home_team, MatchMember.home_id == home_team.id) \
        .outerjoin(away_team, MatchMember.away_id == away_team.id) \
        .outerjoin(child_match, child_match.parent_id == Match.id) \
        .outerjoin(bet_match, or_(bet_match.id == Match.id, bet_match.parent_id == Match.id)) \
        .outerjoin(bet, bet.match_id == bet_match.id) \
        .filter(League.sport_id == sport_id, Match.parent_id.is_(None)) \
        .group_by(Match.id,
                  Match.start_time,
                  League.name,
                  home_team.name,
                  away_team.name,
                  home_team.id,
                  away_team.id,
                  Match.created_at,
                  child_match.id)

    if league_id:
        query = query.filter(League.id == league_id)
    if finished is False:
        query = query.filter(Match.start_time >= utc_now)
    else:
        query = query.filter(Match.start_time < utc_now)
    if nulls is False:
        query = query.having(count_case > 0)
    if hours:
        time_limit = utc_now + timedelta(hours=hours)
        query = query.filter(Match.start_time < time_limit)

    def sort_function(value, sort_order):
        if sort_order.upper() == "ASC":
            return asc(value)
        if sort_order.upper() == "DESC":
            return desc(value)

    if sort_by == "team_name":
        query = query.order_by(sort_function(home_team.name, sort_order))
    elif sort_by == "league_name":
        query = query.order_by(sort_function(League.name, sort_order))
    elif sort_by == "change_count":
        query = query.order_by(sort_function("change_count", sort_order))
    elif sort_by == "last_change":
        query = query.order_by(sort_function("last_update", sort_order))
    elif sort_by == "start_time":
        query = query.order_by(sort_function(Match.start_time, sort_order))

    result = await session.execute(query)

    results = result.fetchall()

    matches = [
        {'id': result[0],
         'start_time': result[1],
         'league_name': result[2],
         'change_count': result[3],
         'last_update': result[4],
         'home_name': result[5],
         'away_name': result[6],
         'event': f"{result[5]} - {result[6]}",
         'home_team_id': result[7],
         'away_team_id': result[8],
         'created_at': result[9],
         'child_id': result[10]}
        for result in results]

    return matches


async def get_child_ids(match_id: int, session: AsyncSession) -> list[int]:
    result = await session.execute(
        select(Match.id).where(Match.parent_id == match_id)
    )
    child_ids = [row[0] for row in result.all()]
    return child_ids

async def get_sport_id_by_match_id(match_id: int, session: AsyncSession) -> int:
    result = await session.execute(
        select(League.sport_id).select_from(Match).join(League, League.id == Match.league_id).filter(Match.id == match_id)
    )
    sport_id = result.scalar_one_or_none()
    return sport_id