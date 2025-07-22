from collections import defaultdict
from typing import Annotated, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.utils import get_period_title
from src.api.dependencies import CURRENT_ACTIVE_USER
from src.core.crud.api.straight import get_changes, get_initial_last_points, get_match
from src.core.db.db_helper import db_helper
import logging

from src.scripts.bet_clusters import group_bets

router = APIRouter(prefix="/straight", tags=["Straight"])

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class Period(BaseModel):
    type: str
    period: int


def group_and_pair_bets(mapped_changes: list[dict[str]]) -> list[list[dict[str]]]:
    grouped_changes = defaultdict(list)
    for change in mapped_changes:
        key = (change['period'], change['type'], change['relation_type'])
        grouped_changes[key].append(change)

    all_pairs = []
    for group in grouped_changes.values():
        sorted_group = sorted(group, key=lambda x: x['created_at'])

        pairs = [
            [sorted_group[i], sorted_group[i + 1]]
            for i in range(len(sorted_group) - 1)
        ]

        all_pairs.extend(pairs)

    all_pairs_sorted = sorted(
        all_pairs,
        key=lambda pair: pair[-1]['created_at']
    )

    return all_pairs_sorted


@router.get("")
async def get_straight_changes(
        current_user: CURRENT_ACTIVE_USER,
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        match_id: int,
        child_id: int | None = None,
):
    match = await get_match(match_id=match_id, session=session)
    match_ids = [match_id, child_id]
    changes = await get_changes(match_ids=match_ids, session=session, periods=[])
    mapped_changes = []
    unique_periods = []
    count_changes_periods = {}
    seen_periods = set()
    for change in changes:
        if change['match_id'] == match_id:
            relation = 'parent'
        elif change['match_id'] == child_id:
            relation = 'child'
        else:
            continue
        period_title = get_period_title(match['match']['sport_id'], change['key'], relation=relation)
        unique_key = (period_title, change['match_id'], change['key'])
        if unique_key in count_changes_periods:
            count_changes_periods[unique_key] += 1
        else:
            count_changes_periods[unique_key] = 0

        if unique_key not in seen_periods:
            seen_periods.add(unique_key)
            unique_periods.append({
                'title': period_title,
                'match_id': change['match_id'],
                'key': change['key'],
                'changes_count': count_changes_periods[unique_key]
            })
        else:
            for period in unique_periods:
                if (period['title'], period['match_id'], period['key']) == unique_key:
                    period['changes_count'] = count_changes_periods[unique_key]
                    break
        change_object = {
            **change,
            'relation_type': relation,
            'period_title': period_title
        }
        mapped_changes.append(change_object)
    mapped_changes = group_bets(mapped_changes)

    comparison = await get_initial_last_points(match_id=match_id, session=session)
    mapped_comparison = []
    for pair in comparison['comparison']:
        result_pair = []
        for comp in pair:
            if comp is None: continue
            if comp['match_id'] == match_id:
                relation = 'parent'
            elif comp['match_id'] == child_id:
                relation = 'child'
            else:
                continue
            period_title = get_period_title(match['match']['sport_id'], comp['key'], relation=relation)
            comp_object = {
                **comp,
                'relation_type': relation,
                'period_title': period_title
            }
            result_pair.append(comp_object)
        mapped_comparison.append(result_pair)
    return {**match, "changes": mapped_changes, "comparison": mapped_comparison, "periods": unique_periods}
