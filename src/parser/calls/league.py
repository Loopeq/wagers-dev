import asyncio
import aiohttp
from aiohttp import ClientTimeout

from src.parser.calls.base import Status, Response
from src.logs import logger

HEADERS = {
    "x-rapidapi-key": "7d2a653207msh4ec37fc83b57e21p19ffd7jsn24288ee9228f",
    "x-rapidapi-host": "pinnacle-odds.p.rapidapi.com"
}
URL = "https://pinnacle-odds.p.rapidapi.com/kit/v1/leagues"


async def _fetch_response():
    async with aiohttp.ClientSession(timeout=ClientTimeout(total=10)) as session:
        async with session.get(URL,
                               headers=HEADERS,
                               params={'sport_id': 3}) as resp:
            if resp.status == 200:
                data = await resp.json()
                return Response(status=Status.ACCEPT, data=data, headers=resp.headers)
            elif resp.status == 404:
                return Response(status=Status.DENIED)
            else:
                return None


async def fetch():
    try:
        response = await _fetch_response()
    except:
        logger.info("Can't connect to https://pinnacle-odds.p.rapidapi.com/kit/v1/leagues")
    else:
        if not response:
            logger.info('Error while "https://pinnacle-odds.p.rapidapi.com/kit/v1/leagues"')
        elif response.status == Status.ACCEPT:
            if response.data.get('leagues'):
                return response.data.get('leagues')
        elif response.status == Status.DENIED:
            logger.info('DENIED while "https://pinnacle-odds.p.rapidapi.com/kit/v1/leagues"')


