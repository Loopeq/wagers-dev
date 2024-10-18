import asyncio
import datetime
from collections import defaultdict
from typing import List

from src.parser.calls.base import Status
from src.parser.calls.straight import get_straight_response
from src.data.crud import MatchOrm, UpdateManager
from src.data.models import BetTypeEnum
from src.data.schemas import MatchUpcomingDTO, BetAddDTO
from src.parser.utils.common import gmt_to_utc, calc_coeff
from src.logs import logger


async def collect_content(matches: List[MatchUpcomingDTO]):
    logger.info(f'Start collecting for {len(matches)} matches')
    tasks = [process_match(match) for match in matches]
    await asyncio.gather(*tasks)
    logger.info(f'Finish collecting for {len(matches)} matches')


async def process_match(match: MatchUpcomingDTO):
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
        if ((w_type == 'moneyline' or w_type == 'team_total')
                or (w_type in un_touch_type and period in un_touch_period.get(w_type))):
            continue

        prices = obj.get('prices')
        point = max(prices[0].get('points'), prices[1].get('points'))
        un_touch_type.append(w_type)
        un_touch_period[w_type].append(period)
        home_price = calc_coeff(prices[0].get('price'))
        away_price = calc_coeff(prices[1].get('price'))

        bets.append(
            BetAddDTO(match_id=match.id,
                      point=point,
                      home_cf=home_price,
                      away_cf=away_price,
                      type=BetTypeEnum[w_type],
                      period=period,
                      created_at=response_date))
    await UpdateManager.insert_bets(bets)
