from src.scripts.bet_clusters import group_bets
from src.core.crud.api.straight import get_changes, get_initial_last_points, get_match
from fastapi import HTTPException
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.utils import get_period_title
from src.core.crud.api.straight import get_team_games
import json
from src.analyzer.analyzer import get_analyzed


def group_and_pair_bets(mapped_changes: list[dict[str]]) -> list[list[dict[str]]]:
    grouped_changes = defaultdict(list)
    for change in mapped_changes:
        key = (change["period"], change["type"], change["relation_type"])
        grouped_changes[key].append(change)

    all_pairs = []
    for group in grouped_changes.values():
        sorted_group = sorted(group, key=lambda x: x["created_at"])

        pairs = [
            [sorted_group[i], sorted_group[i + 1]] for i in range(len(sorted_group) - 1)
        ]

        all_pairs.extend(pairs)

    all_pairs_sorted = sorted(all_pairs, key=lambda pair: pair[-1]["created_at"])

    return all_pairs_sorted


def get_mapped_changes(changes: list, match_id: int, child_id: int, sport_id: int):
    mapped_changes = []
    unique_periods = []
    count_changes_periods = {}
    seen_periods = set()

    for change in changes:
        if change["match_id"] == match_id:
            relation = "parent"
        elif change["match_id"] == child_id:
            relation = "child"
        else:
            continue
        period_title = get_period_title(sport_id, change["key"], relation=relation)
        unique_key = (period_title, change["match_id"], change["key"])
        if unique_key in count_changes_periods:
            count_changes_periods[unique_key] += 1
        else:
            count_changes_periods[unique_key] = 0

        if unique_key not in seen_periods:
            seen_periods.add(unique_key)
            unique_periods.append(
                {
                    "title": period_title,
                    "match_id": change["match_id"],
                    "key": change["key"],
                    "changes_count": count_changes_periods[unique_key],
                }
            )
        else:
            for period in unique_periods:
                if (period["title"], period["match_id"], period["key"]) == unique_key:
                    period["changes_count"] = count_changes_periods[unique_key]
                    break
        change_object = {
            **change,
            "relation_type": relation,
            "period_title": period_title,
        }
        mapped_changes.append(change_object)
    return group_bets(mapped_changes), unique_periods


async def get_mapped_comparison(
    comparison: dict, match_id: int, child_id: int, sport_id: int
):
    mapped_comparison = []
    for pair in comparison["comparison"]:
        result_pair = []
        for comp in pair:
            if comp is None:
                continue
            if comp["match_id"] == match_id:
                relation = "parent"
            elif comp["match_id"] == child_id:
                relation = "child"
            else:
                continue
            period_title = get_period_title(sport_id, comp["key"], relation=relation)
            comp_object = {
                **comp,
                "relation_type": relation,
                "period_title": period_title,
            }
            result_pair.append(comp_object)
        mapped_comparison.append(result_pair)
    return mapped_comparison


async def get_straight(match_id: int, child_id: int, session: AsyncSession):
    try:
        match = await get_match(match_id=match_id, session=session)
    except:
        raise HTTPException(404, detail="Not found")
    match_ids = [match_id, child_id]
    changes = await get_changes(match_ids=match_ids, session=session, periods=[])
    mapped_changes, unique_periods = get_mapped_changes(
        changes=changes,
        match_id=match_id,
        child_id=child_id,
        sport_id=match["match"]["sport_id"],
    )

    comparison = await get_initial_last_points(
        match_id=match_id, child_id=child_id, session=session
    )

    mapped_comparison = await get_mapped_comparison(
        comparison=comparison,
        match_id=match_id,
        child_id=child_id,
        sport_id=match["match"]["sport_id"],
    )
    return {
        **match,
        "changes": mapped_changes,
        "comparison": mapped_comparison,
        "periods": unique_periods,
    }


async def get_straight_full_history(
    match_id: int, child_id: int, session: AsyncSession
):
    default_straight = await get_straight(
        match_id=match_id, child_id=child_id, session=session
    )
    default_straight["match_result"] = None
    current_match_id = default_straight["match"]["match_id"]
    home_id = default_straight["match"]["home_team_id"]
    away_id = default_straight["match"]["away_team_id"]
    home_name = default_straight["match"]["home_name"]
    away_name = default_straight["match"]["away_name"]

    home_history = await get_team_games(
        team_id=home_id, current_match_id=current_match_id, session=session
    )
    away_history = await get_team_games(
        team_id=away_id, current_match_id=current_match_id, session=session
    )

    for home_event in home_history:
        event_id = home_event["id"]
        event_child_id = home_event["child_id"]
        event_straight = await get_straight(
            match_id=event_id, child_id=event_child_id, session=session
        )
        home_event["straight"] = event_straight

    for away_event in away_history:
        event_id = away_event["id"]
        event_child_id = away_event["child_id"]
        event_straight = await get_straight(
            match_id=event_id, child_id=event_child_id, session=session
        )
        away_event["straight"] = event_straight

    full_history = {
        **default_straight,
        "home_history": home_history,
        "away_history": away_history,
    }
    tool_call_query = f"{home_name} vs {away_name} tennis"
    full_history_dump = json.dumps(full_history, default=str)
    analyzed = await get_analyzed(
        content=full_history_dump, tool_call_query=tool_call_query
    )
    return analyzed
