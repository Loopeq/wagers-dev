from datetime import datetime, timedelta
import math
from typing import Annotated
from curl_cffi import AsyncSession
from fastapi import APIRouter, Depends
from sqlalchemy import asc, case, desc, distinct, func, or_, select
from sqlalchemy.orm import aliased
from src.api.repositories.straight import get_straight
from src.core.db.db_helper import db_helper
from src.api.dependencies import CURRENT_ACTIVE_USER
from src.core.models import Bet, League, Match, MatchMember, Sport, Team
from src.core.schemas import SportDTO

router = APIRouter(prefix="/market", tags=["Market"])

@router.get("/sports", response_model=list[SportDTO])
async def load_sports(
    current_user: CURRENT_ACTIVE_USER,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    stmt = (
        select(
            Sport.id, 
            Sport.name, 
            func.count(Match.id).label("match_count")
        )
        .outerjoin(League, League.sport_id == Sport.id)
        .outerjoin(Match, Match.league_id == League.id)
        .where(Match.start_time > datetime.utcnow())
        .group_by(Sport.id, Sport.name)
        .order_by(desc(func.count(Match.id)))
    )

    result = await session.execute(stmt)
    return [
        {"id": s.id, "name": s.name.title(), "match_count": s.match_count}
        for s in result.all()
    ]

@router.get("/related")
async def get_related(
    current_user: CURRENT_ACTIVE_USER,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    sport_id: int,
    league_id: int | None = None,
    hours: int | None = None,
    finished: bool | None = False,
    nulls: bool | None = False,
    sort_by: str | None = "team_name",
    sort_order: str | None = "ASC",
    offset: int | None = 0,
    limit: int | None = 20,
):
    utc_now = datetime.utcnow()

    bet_match = aliased(Match)
    bet = aliased(Bet)

    match_counts_query = (
        select(
            League.sport_id,
            func.count(distinct(Match.id)).label("upcoming_matches_with_changes"),
        )
        .outerjoin(Match, League.id == Match.league_id)
        .outerjoin(bet_match, or_(bet_match.id == Match.id, bet_match.parent_id == Match.id))
        .outerjoin(bet, bet.match_id == bet_match.id)
        .filter(Match.start_time > utc_now, Match.parent_id.is_(None), bet.version >= 1)
        .group_by(League.sport_id)
    )
    result = await session.execute(match_counts_query)
    match_counts = [{"sport_id": row[0], "count": row[1]} for row in result.fetchall()]

    home_team = aliased(Team)
    away_team = aliased(Team)
    child_match = aliased(Match)

    count_case = func.count(case((bet.version >= 1, bet.id), else_=None))
    last_update = func.max(bet.created_at).filter(bet.version >= 1)

    query = (
        select(
            Match.id,
            Match.start_time,
            League.name.label("league_name"),
            count_case.label("change_count"),
            last_update.label("last_update"),
            home_team.name.label("home_name"),
            away_team.name.label("away_name"),
            home_team.id.label("home_team_id"),
            away_team.id.label("away_team_id"),
            Match.created_at,
            child_match.id.label("child_id"),
        )
        .outerjoin(League, League.id == Match.league_id)
        .outerjoin(MatchMember, MatchMember.match_id == Match.id)
        .outerjoin(home_team, MatchMember.home_id == home_team.id)
        .outerjoin(away_team, MatchMember.away_id == away_team.id)
        .outerjoin(child_match, child_match.parent_id == Match.id)
        .outerjoin(bet_match, or_(bet_match.id == Match.id, bet_match.parent_id == Match.id))
        .outerjoin(bet, bet.match_id == bet_match.id)
        .filter(League.sport_id == sport_id, Match.parent_id.is_(None))
        .group_by(
            Match.id,
            Match.start_time,
            League.name,
            home_team.name,
            away_team.name,
            home_team.id,
            away_team.id,
            Match.created_at,
            child_match.id,
        )
    )

    if league_id:
        query = query.filter(League.id == league_id)
    query = query.filter(Match.start_time >= utc_now if not finished else Match.start_time < utc_now)
    if hours:
        query = query.filter(Match.start_time < utc_now + timedelta(hours=hours))
    if not nulls:
        query = query.having(count_case > 0)

    sort_map = {
        "team_name": home_team.name,
        "league_name": League.name,
        "change_count": count_case,
        "last_change": last_update,
        "start_time": Match.start_time,
    }
    sort_col = sort_map.get(sort_by, home_team.name)
    query = query.order_by(asc(sort_col) if sort_order.upper() == "ASC" else desc(sort_col))

    results = (await session.execute(query)).fetchall()

    matches = [
        {
            "id": row.id,
            "start_time": row.start_time,
            "league_name": row.league_name,
            "change_count": row.change_count,
            "last_update": row.last_update,
            "home_name": row.home_name,
            "away_name": row.away_name,
            "event": f"{row.home_name} - {row.away_name}",
            "home_team_id": row.home_team_id,
            "away_team_id": row.away_team_id,
            "created_at": row.created_at,
            "child_id": row.child_id,
        }
        for row in results
    ]

    pagination = {
        "pages": math.ceil(len(matches) / limit) if limit else 1,
        "current_page": (offset // limit + 1) if limit else 1,
    }

    return {
        "matches": matches[offset : offset + limit] if limit else matches,
        "match_counts": match_counts,
        "pagination": pagination,
    }


@router.get("/straight")
async def load_straight(
    current_user: CURRENT_ACTIVE_USER,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    match_id: int,
    child_id: int | None = None,
):
    straight = await get_straight(match_id=match_id, child_id=child_id, session=session)
    return straight
