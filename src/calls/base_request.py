import asyncio
import enum
from typing import Any, List

import aiohttp
from aiohttp import ContentTypeError, ClientError
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
    data: Any
    headers: Any = {}
    errors: List[Error] = []


async def get_request(url: str, headers: dict, timeout: float = 1.5,
                      between_timeout: float = 1.0) -> Response:
    pm = ProxyManager()

    async with aiohttp.ClientSession() as session:

        logger.info(msg=f'Make request from {url}')

        while True:
            _errors = []
            trace = {'proxy': pm.proxy, 'url': url}
            try:
                async with session.get(url,
                                       headers=headers,
                                       proxy=pm.proxy,
                                       timeout=timeout) as resp:
                    try:
                        data = await resp.json()
                    except ContentTypeError as error:
                        _errors.append(Error(msg=error.message, kwargs=trace))
                    except Exception as error:
                        _errors.append(Error(msg=str(error), kwargs=trace))
                    finally:
                        pm.update()
                        if data:
                            logger.info(f'Return response for url: {url}')
                            return Response(status=Status.ACCEPT, data=data, headers=resp.headers, errors=_errors)

            except TimeoutError as error:
                _errors.append(Error(msg=str(error), kwargs=trace))
            except ClientError as error:
                _errors.append(Error(msg=str(error), kwargs=trace))
            except NoValidProxyError as error:
                _errors.append(Error(msg=str(error), kwargs=trace))
                return Response(status=Status.DENIED, data=[], headers=resp.headers, errors=_errors)
            except Exception as error:
                _errors.append(Error(msg=str(error), kwargs=trace))
            finally:
                pm.update()

            await asyncio.sleep(between_timeout)
