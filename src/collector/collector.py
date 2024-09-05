import asyncio

from src.calls.base_request import Status
from src.calls.matchups import get_match_up_response
from src.calls.straight import get_straight_response
from src.collector.content import collect_straight_content, save_straight_content
from src.collector.header import collect_match_headers, save_match_header


async def collect():
    match_ups_response = await get_match_up_response(4)
    headers = await collect_match_headers(data=match_ups_response.data)

    for header in headers:
        match_dir = save_match_header(header)
        match_id = header['match_id']
        straight_response = await get_straight_response(match_id=match_id)
        straight_content = await collect_straight_content(data=straight_response.data, header=straight_response.headers)
        await save_straight_content(straight_content, match_dir=match_dir)

if __name__ == "__main__":
    asyncio.run(collect())
