import asyncio
from time import time

import aiohttp
from aiohttp import ContentTypeError, ClientError
from asyncio import TimeoutError
from proxy import NoValidProxyError
from src.proxy import proxy_manager
from aiocache import cached
import re

HEADERS = {
    'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    'X-Device-UUID': '6d702fee-ff3e303d-e0986d30-b379cb05',
    'sec-ch-ua-mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Referer': 'https://www.pinnacle.com/',
    'X-API-Key': 'CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R',
    'sec-ch-ua-platform': '"Linux"',
}

URL = 'https://guest.api.arcadia.pinnacle.com/0.1/matchups/{0}/markets/related/straight'


def key_to_string(key: str):
    # pattern = {
    #     'm': 'MoneyLine',
    #     'ou': 'Total',
    #     's': 'Spread'
    # }

    match = re.search(r';(\d+);(\w+)', key)
    return match.group(1), match.group(2)


def calculate_coefficient(price):
    if price > 0:
        return round(price / 100 + 1, 3)
    return round(abs(100 / price) + 1, 3)


def get_straight_info(straight_content: list[dict]):

    if straight_content is None:
        raise Exception('straight content is None')

    dct = {}
    for current in straight_content:
        prices = current['prices']
        str_key = key_to_string(current['key'])

        for price_obj in prices:
            price = price_obj['price']
            coeff = calculate_coefficient(price)

            temp = {'designation': price_obj['designation'],
                    'points': price_obj.get('points'),
                    'coeff': coeff
                    }

            dct.setdefault(str_key, []).append(temp)
    return dct


@cached(ttl=10)
async def get_straight_content_request(match_id):
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(URL.format(match_id),
                                       headers=HEADERS,
                                       proxy=proxy_manager.proxy,
                                       timeout=1.5) as resp:
                    if resp.status == 200:
                        try:
                            data = await resp.json()
                            return data
                        except ContentTypeError as error:
                            print(error)
                            return None
                        except Exception as error:
                            print('Unexpected error with read json', error)

                    proxy_manager.update()

            except TimeoutError as error:
                print(f"Timeout with proxy: {proxy_manager.proxy} ", error)
                proxy_manager.update()
            except ClientError as error:
                print(f"Client error with proxy: {proxy_manager.proxy} ", error)
                proxy_manager.update()
            except NoValidProxyError as error:
                print(f'No valid proxy: {error}')
            except Exception as error:
                print(f'Unexpected error with proxy: {proxy_manager.proxy} ', error)

            await asyncio.sleep(1)


async def main():
    straight_response = await get_straight_content_request(1595892404)
    try:
        straight_info = get_straight_info(straight_content=straight_response)
        print(straight_info)
    except Exception as Error:
        print(Error)

if __name__ == "__main__":
    asyncio.run(main())
