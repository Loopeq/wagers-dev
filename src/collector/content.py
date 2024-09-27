import asyncio
import json
import logging
import random
from collections import defaultdict
from datetime import timedelta
from typing import List

from src.calls.base import Status
from src.calls.matchups import get_match_up_response
from src.calls.straight import get_straight_response
from src.collector.heads import collect_heads
from src.data.crud import MatchOrm, UpdateManager
from src.data.models import BetTypeEnum, BetStatusEnum, BetValueTypeEnum
from src.data.schemas import MatchUpcomingDTO, BetAddDTO
from src.utils.common import gmt_to_utc, calc_coeff


async def collect_content(matches: List[MatchUpcomingDTO]):
    for match in matches:

        content_response = await get_straight_response(match_id=match.id)

        if content_response.status == Status.DENIED:
            continue

        headers = content_response.headers
        data = content_response.data
        response_date = gmt_to_utc(headers.get('Date'))
        bets = []
        un_touch_type = []
        un_touch_period = defaultdict(list)
        for obj in data:
            w_type = obj.get('type')
            period = obj.get('period')
            if (w_type == 'moneyline') or (w_type in un_touch_type and period in un_touch_period.get(w_type)):
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


async def _dev():
    matches = await MatchOrm.get_upcoming_matches()
    res = await collect_content(matches=matches)


if __name__ == "__main__":
    asyncio.run(_dev())
