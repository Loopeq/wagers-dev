from dataclasses import dataclass
from typing import Any, Optional
import aiohttp
from asyncio import TimeoutError

from aiohttp import TCPConnector

from src.parser.utils.proxy import ProxyManager

pm = ProxyManager()
max_retries = 10


@dataclass
class Response:
    status: int
    data: Any = None
    headers: Optional[dict] = None


async def get_request(url: str, headers: dict, params: dict = None, cookies: dict = None, use_proxy: bool = True) -> Response:
    connector = TCPConnector(limit=2000)
    async with aiohttp.ClientSession(connector=connector, cookies=cookies) as session:
        for _ in range(max_retries):
            proxy = None
            if use_proxy:
                proxy = pm.proxy
            try:
                async with session.get(url,
                                       headers=headers,
                                       params=params,
                                       proxy=proxy,
                                       timeout=5) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        return Response(status=resp.status, data=response, headers=dict(resp.headers))
                    elif resp.status == 404:
                        return Response(status=resp.status)
            except (aiohttp.ContentTypeError, TimeoutError, aiohttp.ClientError):
                continue
        return Response(status=404)
