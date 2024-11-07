import asyncio
import aiohttp
from src.parser.calls.base import Response, Status

HEADERS = {
    "x-rapidapi-key": "7d2a653207msh4ec37fc83b57e21p19ffd7jsn24288ee9228f",
    "x-rapidapi-host": "pinnacle-odds.p.rapidapi.com"
}
URL = "https://pinnacle-odds.p.rapidapi.com/kit/v1/details"


async def _get_match_details_response(event_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(URL,
                               headers=HEADERS,
                               params={'event_id': event_id}) as resp:
            if resp.status == 200:
                data = await resp.json()
                return Response(status=Status.ACCEPT, data=data, headers=resp.headers)
            elif resp.status == 404:
                return Response(status=Status.DENIED)
            else:
                return None


async def get_match_details(event_id: int):
    response = await _get_match_details_response(event_id=event_id)
    if not response:
        return None

    if response.status == Status.ACCEPT:
        if response.data.get('events'):
            return response.data.get('events')[0].get('period_results')
    return None


