import asyncio
import json
from src.data.crud import MatchOrm, MatchMemberOrm, BetOrm, BetValueOrm
from src.calls.base import Status
from src.calls.matchups import get_match_up_response
from src.calls.straight import get_straight_response
from src.data.models import BetTypeEnum, BetStatusEnum, BetValueTypeEnum
from src.data.schemas import BetValueAddDTO, MatchUpcomingDTO
from src.utils.common import gmt_to_utc, calc_coeff


async def collect_content(matches: List[MatchUpcomingDTO]):
    for match in matches:
        content_response = await get_straight_response(match_id=match.id)
        headers = content_response.headers
        data = content_response.data
        response_date = gmt_to_utc(headers.get('Date'))
        bet_group = []
        for content in data:
            w_type = BetTypeEnum[content['type'].lower()]
            period = content.get('period')
            match_id = content.get('matchupId')

            bet_id = await BetOrm.get_bet_id_by_(bet_type=w_type, period=period, match_id=match_id)
            prices = content['prices']
            status = content.get('status')
            bet_values = []
            for price in prices:
                design = price.get('designation')
                points = price.get('points')
                coeff = calc_coeff(price['price'])

                bet_values.append(BetValueAddDTO(bet_id=bet_id,
                                                 value=coeff,
                                                 point=points,
                                                 status=BetStatusEnum[status],
                                                 created_at=response_date,
                                                 type=BetValueTypeEnum[design]))
            bet_group.append(bet_values)
        await BetValueOrm.insert_bet_values(bet_group)


if __name__ == "__main__":
    asyncio.run(collect_content())
