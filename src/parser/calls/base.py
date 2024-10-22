import enum
from typing import Any
import aiohttp
from aiohttp import ContentTypeError, ClientError
from asyncio import TimeoutError
from src.parser.utils.proxy import ProxyManager, NoValidProxyError
from pydantic import BaseModel


class Status(enum.Enum):
    ACCEPT = 200
    DENIED = 400


class Response(BaseModel):
    status: Status
    data: Any = []
    headers: Any = {}


async def get_request(url: str, headers: dict, timeout: float = 3.0, params: dict = None) -> Response:
    pm = ProxyManager()
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(url,
                                       headers=headers,
                                       params=params,
                                       proxy=pm.proxy,
                                       timeout=timeout) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return Response(status=Status.ACCEPT, data=data, headers=resp.headers)
                    elif resp.status == 404:
                        return Response(status=Status.DENIED)
                    else:
                        pm.update()

            except (ContentTypeError, TimeoutError, ClientError):
                pm.update()
            except NoValidProxyError:
                return Response(status=Status.DENIED, headers=resp.headers)
            except Exception:
                pm.update()
