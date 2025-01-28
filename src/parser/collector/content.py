import asyncio
import datetime
from collections import defaultdict
from src.core.crud.parser.match import get_upcoming_matches
from src.core.crud.parser.bet import insert_bets
from src.parser.base import Status
from src.parser.calls.straight import get_straight_response
from src.core.models import BetTypeEnum
from src.core.schemas import MatchUpcomingDTO, BetAddDTO
from src.parser.utils.common import gmt_to_utc, calc_coeff


async def collect_content(start, end, parse_allow_types: list):
    stmd = datetime.timedelta(hours=start) if start else None
    edmd = datetime.timedelta(hours=end) if end else None
    matches = await get_upcoming_matches(start_timedelta=stmd, end_timedelta=edmd)

    completed_matches_count = 0

    async def process_and_count(match):
        nonlocal completed_matches_count
        await process_match(match, parse_allow_types=parse_allow_types)
        completed_matches_count += 1

    tasks = [process_and_count(match) for match in matches]

    if tasks:
        await asyncio.gather(*tasks)
    else:
        pass


async def process_match(match: MatchUpcomingDTO, parse_allow_types: list):
    content_response = await get_straight_response(match_id=match.id)
    time_now = datetime.datetime.utcnow()

    if content_response.status == Status.DENIED or match.start_time < time_now:
        return

    headers = content_response.headers
    data = content_response.data
    response_date = gmt_to_utc(headers.get('Date'))
    bets = []
    un_touch_type = []
    un_touch_period = defaultdict(list)
    for obj in data:
        w_type = obj.get('type')
        period = obj.get('period')
        if (w_type not in parse_allow_types
                or (w_type in un_touch_type and period in un_touch_period.get(w_type))):
            continue

        prices = obj.get('prices')
        point = prices[0].get('points')
        home_price = calc_coeff(prices[0].get('price'))
        away_price = calc_coeff(prices[1].get('price'))

        un_touch_type.append(w_type)
        un_touch_period[w_type].append(period)

        bets.append(
            BetAddDTO(match_id=match.id,
                      point=point,
                      home_cf=home_price,
                      away_cf=away_price,
                      type=BetTypeEnum[w_type],
                      period=period,
                      created_at=response_date))
    await insert_bets(bets=bets, match_id=match.id)
