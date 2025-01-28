import logging

import aiohttp
from aiohttp import ClientTimeout
from src.core.settings import settings
from src.parser.base import Status, Response

HEADERS = {
    "x-rapidapi-key": settings.RAPID_KEY,
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
        logging.warning("Can't connect to https://pinnacle-odds.p.rapidapi.com/kit/v1/leagues")
    else:
        if not response:
            logging.warning('Error while "https://pinnacle-odds.p.rapidapi.com/kit/v1/leagues"')
        elif response.status == Status.ACCEPT:
            if response.data.get('leagues'):
                return response.data.get('leagues')
        elif response.status == Status.DENIED:
            logging.warning('DENIED while "https://pinnacle-odds.p.rapidapi.com/kit/v1/leagues"')


