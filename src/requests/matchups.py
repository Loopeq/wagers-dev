from src.requests.base import get_request
from src.core.logger import get_module_logger
import asyncio

HEADERS = {
    'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    'X-Device-UUID': '6d702fee-ff3e303d-e0986d30-b379cb05',
    'sec-ch-ua-mobile': '?0',
    'User-Agent':
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Referer': 'https://www.pinnacle.com/',
    'X-API-Key': 'CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R',
    'sec-ch-ua-platform': '"Linux"',
}

PARAMS = {
    'withSpecials': 'false',
    'brandId': '0',
}

URL = 'https://guest.api.arcadia.pinnacle.com/0.1/sports/{0}/matchups'

logger = get_module_logger(__name__)

async def get_match_up_response(event_id: int):
    response = await get_request(url=URL.format(event_id), headers=HEADERS)
    if response.status != 200:
        logger.error(f'Error fetching {URL.format(event_id)}')
    return response


if __name__ == "__main__":
    asyncio.run(get_match_up_response(33))
