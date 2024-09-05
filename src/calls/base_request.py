import asyncio
import enum
from typing import Any, List
from fake_useragent import UserAgent
import aiohttp
from aiohttp import ClientTimeout
from aiohttp import ContentTypeError, ClientError, ClientResponse
from requests import ConnectionError
from asyncio import TimeoutError

from src.calls.logs import logger
from src.proxy import ProxyManager, NoValidProxyError
from pydantic import BaseModel


class Status(enum.Enum):
    ACCEPT = 200
    DENIED = 400


class Error(BaseModel):
    msg: str
    kwargs: dict


class Response(BaseModel):
    status: Status
    data: Any = []
    headers: Any = {}


async def get_request(url: str, headers: dict, timeout: float = 5.0) -> Response:
    pm = ProxyManager()
    async with aiohttp.ClientSession() as session:
        logger.info(msg=f'Make request for {url}')
        while True:
            try:
                async with session.get(url,
                                       headers=headers,
                                       proxy=pm.proxy,
                                       timeout=timeout) as resp:
                    if resp.status == 200:
                        logger.info(f'Return response from url: {url}')
                        data = await resp.json()

                        return Response(status=Status.ACCEPT, data=data, headers=resp.headers)
                    pm.update()
            except (ContentTypeError, TimeoutError, ClientError):
                pm.update()
            except NoValidProxyError as err:
                logger.error(f'No valid proxy found with err {err}')
                return Response(status=Status.DENIED, headers=resp.headers)
            except Exception as err:
                logger.error(f'Unexpected exception with err {err}')
                pm.update()
