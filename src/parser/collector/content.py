import asyncio
import datetime
from src.core.logger import get_module_logger
from src.core.crud.parser.match import get_upcoming_matches
from src.core.crud.parser.bet import (
    insert_bets_points,
    insert_bets_coeffs,
    get_event_bets,
)
from src.core.utils import format_key
from src.parser.config import sports, sports_ids
from src.requests.straight import get_straight_response
from src.core.schemas import MatchUpcomingDTO, BetAddDTO
from src.parser.utils.common import calc_coeff
from src.scripts.bet_clusters import extract_latest, is_int_or_half

logger = get_module_logger(__name__)


async def collect_content():
    matches = await get_upcoming_matches()
    response_date = datetime.datetime.utcnow()
    if matches:
        stack = []
        for match in matches:
            if match.sport_id == sports["basketball"]:
                stack.append(process_match_basketball(match, response_date))
            elif match.sport_id == sports["tennis"]:
                stack.append(process_match_tennis(match, response_date))
            elif match.sport_id == sports["football"]:
                stack.append(process_match_football(match, response_date))
        await asyncio.gather(*stack)


async def extract_bet_content(
    match: MatchUpcomingDTO, response_date: datetime.datetime
):
    bets = []
    seen_bets = set()
    content_response = await get_straight_response(match_id=match.id)
    all_event_bets = await get_event_bets(match_id=match.id)
    latest_bets = extract_latest(all_event_bets)
    if content_response.status == 404 or match.start_time < response_date:
        return
    for obj in content_response.data:
        matchupId = obj.get("matchupId")
        if matchupId != match.id:
            continue
        w_type = obj.get("type")
        period = obj.get("period")
        key = format_key(obj.get("key"))
        # для team_total
        if w_type == "team_total":
            side = obj.get("key").split(";")[-1]
            key += side
        bet_key = (w_type, period, key, matchupId)
        prices = obj.get("prices", [])
        if len(prices) < 2:
            continue
        point = prices[0].get("points")
        if sports_ids.get(match.sport_id) in ["tennis"] and match.parent_id:
            if key not in ["s;0;ou"]:
                continue
        if sports_ids.get(match.sport_id) in ["football", "tennis"]:
            if bet_key in seen_bets:
                continue

            if point is None:
                seen_bets.add(bet_key)
            else:
                latest = latest_bets.get(key)
                if not is_int_or_half(point):
                    continue
                if latest:
                    if latest.point != point:
                        continue
                seen_bets.add(bet_key)
        else:
            if obj.get("isAlternate", True):
                continue
            if bet_key in seen_bets:
                continue
            seen_bets.add(bet_key)
        limits = obj.get("limits")[0]
        limit_max = limits.get("amount")
        home_price = calc_coeff(prices[0]["price"])
        away_price = calc_coeff(prices[1]["price"])
        draw_price = None
        if len(prices) == 3:
            draw_price = calc_coeff(prices[2]["price"])

        bets.append(
            BetAddDTO(
                match_id=match.id,
                point=point,
                max_limit=limit_max,
                home_cf=home_price,
                draw_cf=draw_price,
                away_cf=away_price,
                type=w_type,
                period=period,
                key=key,
                created_at=response_date,
            )
        )
    return bets


async def process_match_basketball(
    match: MatchUpcomingDTO, response_date: datetime.datetime
):
    bets = await extract_bet_content(match, response_date)
    if bets:
        await insert_bets_points(bets=bets, match_id=match.id)


async def process_match_tennis(
    match: MatchUpcomingDTO, response_date: datetime.datetime
):
    bets = await extract_bet_content(match, response_date)
    if bets:
        await insert_bets_coeffs(bets=bets)


async def process_match_football(
    match: MatchUpcomingDTO, response_date: datetime.datetime
):
    bets = await extract_bet_content(match, response_date)
    if bets:
        await insert_bets_coeffs(bets=bets)
