from sqlalchemy import select, func, or_, and_, distinct, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.core.models import Bet, Match, League, MatchMember, Team, MatchResult


async def get_match(match_id: int, session: AsyncSession):
    home_team = aliased(Team)
    away_team = aliased(Team)
    query = (
        select(
            Match.id,
            Match.league_id,
            Match.start_time,
            League.name,
            League.sport_id,
            home_team.id.label("home_member_id"),
            away_team.id.label("away_member_id"),
            home_team.name.label("home_name"),
            away_team.name.label("away_name"),
        )
        .select_from(Match)
        .outerjoin(League, League.id == Match.league_id)
        .outerjoin(MatchMember, MatchMember.match_id == Match.id)
        .outerjoin(home_team, MatchMember.home_id == home_team.id)
        .outerjoin(away_team, MatchMember.away_id == away_team.id)
        .filter(Match.id == match_id)
    )
    result = await session.execute(query)
    match = result.fetchone()
    match_dto = {
        "match_id": match[0],
        "league_id": match[1],
        "start_time": match[2],
        "league_name": match[3],
        "sport_id": match[4],
        "home_team_id": match[5],
        "away_team_id": match[6],
        "home_name": match[7],
        "away_name": match[8],
    }

    result_query = (
        select(
            MatchResult.period,
            MatchResult.description,
            MatchResult.team_1_score,
            MatchResult.team_2_score,
        )
        .where(MatchResult.match_id == match_id)
        .order_by(MatchResult.period)
    )

    result_rows = await session.execute(result_query)
    results = result_rows.fetchall()

    match_results = [
        {
            "period": r[0],
            "description": r[1],
            "team_1_score": r[2],
            "team_2_score": r[3],
        }
        for r in results
    ]

    return {"match": match_dto, "match_results": match_results}


async def get_changes(match_ids: list, periods: list | None, session: AsyncSession):
    query = select(Bet).filter(
        Bet.match_id.in_(match_ids),
    )
    if periods:
        query = query.filter(Bet.key.in_(periods))
    query = query.order_by(Bet.created_at.desc())
    result = await session.execute(query)
    bets = result.scalars().all()

    changes = [bet.__dict__ for bet in bets]
    for change in changes:
        change.pop("_sa_instance_state", None)
    return changes


async def get_initial_last_points(match_id: int, child_id: int, session: AsyncSession):
    max_version_subq = (
        select(
            Bet.period, Bet.type, Bet.key, func.max(Bet.version).label("max_version")
        )
        .filter(
            or_(Bet.match_id == match_id, Bet.match_id == child_id), Bet.version != 0
        )
        .group_by(Bet.period, Bet.type, Bet.key)
        .subquery()
    )

    bet_alias = aliased(Bet)

    query = (
        select(bet_alias)
        .outerjoin(
            max_version_subq,
            and_(
                bet_alias.period == max_version_subq.c.period,
                bet_alias.type == max_version_subq.c.type,
            ),
        )
        .filter(
            or_(bet_alias.match_id == match_id, bet_alias.match_id == child_id),
            or_(
                bet_alias.version == 0,
                bet_alias.version == max_version_subq.c.max_version,
            ),
        )
        .order_by(bet_alias.type, bet_alias.period)
    )

    result = await session.execute(query)
    bets = result.scalars().all()

    bets = [bet.__dict__ for bet in bets]
    for bet in bets:
        bet.pop("_sa_instance_state", None)
    grouped_bets = {}
    for bet in bets:
        key = (bet["match_id"], bet["period"], bet["type"], bet["key"])
        if key not in grouped_bets:
            grouped_bets[key] = []
        grouped_bets[key].append(bet)

    result_array = []
    for key, bet_list in grouped_bets.items():
        bet_list.sort(key=lambda x: x["version"])
        if len(bet_list) == 2:
            result_array.append((bet_list[0], bet_list[1]))
        elif len(bet_list) == 1:
            result_array.append((bet_list[0], None))

    return {"comparison": result_array}


async def get_team_games(team_id: int, current_match_id: int, session: AsyncSession):
    HomeTeam = aliased(Team)
    AwayTeam = aliased(Team)
    child_match = aliased(Match)
    match_result_subq = select(MatchResult).where(MatchResult.period == 0).subquery()
    count_case = func.count(case((Bet.version >= 1, Bet.id), else_=None))
    stmt = (
        select(
            Match.id,
            Match.start_time,
            Match.created_at,
            League.name.label("league_name"),
            HomeTeam.name.label("home_team_name"),
            AwayTeam.name.label("away_team_name"),
            HomeTeam.id.label("home_team_id"),
            AwayTeam.id.label("away_team_id"),
            child_match.id.label("child_id"),
            match_result_subq.c.description.label("result_title"),
            match_result_subq.c.team_1_score.label("home_score"),
            match_result_subq.c.team_2_score.label("away_score"),
            count_case.label("change_count"),
        )
        .join(MatchMember, Match.id == MatchMember.match_id)
        .join(League, League.id == Match.league_id)
        .join(HomeTeam, HomeTeam.id == MatchMember.home_id)
        .join(AwayTeam, AwayTeam.id == MatchMember.away_id)
        .outerjoin(Bet, Bet.match_id == Match.id)
        .outerjoin(
            match_result_subq, match_result_subq.c.match_id == MatchMember.match_id
        )
        .outerjoin(child_match, child_match.parent_id == Match.id)
        .filter(
            or_(
                MatchMember.home_id == team_id,
                MatchMember.away_id == team_id,
            ),
            Match.id != current_match_id,
        )
        .order_by(Match.start_time.desc())
        .group_by(
            Match.id,
            League.name,
            HomeTeam.name,
            AwayTeam.name,
            HomeTeam.id,
            AwayTeam.id,
            child_match.id,
            match_result_subq.c.description,
            match_result_subq.c.team_1_score,
            match_result_subq.c.team_2_score,
            match_result_subq.c.team_2_score,
        )
    )

    result = await session.execute(stmt)
    rows = result.all()
    return [
        {
            "id": row.id,
            "start_time": row.start_time,
            "league_name": row.league_name,
            "home_name": row.home_team_name,
            "away_name": row.away_team_name,
            "home_team_id": row.home_team_id,
            "away_team_id": row.away_team_id,
            "child_id": row.child_id,
            "result_title": row.result_title,
            "home_score": row.home_score,
            "away_score": row.away_score,
            "change_count": row.change_count,
        }
        for row in rows
    ]
