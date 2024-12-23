import aiohttp
from webshare import ApiClient
from pathlib import Path
from src.settings import settings as conf
import requests

_CLIENT = ApiClient(conf.WEBSHARE_API)
_PROXIES = _CLIENT.get_proxy_list().get_results()


class NoValidProxyError(Exception):
    """When all proxies are invalid"""
    pass


class ProxyManager:
    # (0) username (1) password (2) ip (3) port
    _SCHEMA = 'http://{0}:{1}@{2}:{3}'

    def __init__(self):
        self._proxy_list = _PROXIES
        self._current_id = 0

    def _fetch_proxy(self):
        return self._proxy_list[self._current_id]

    @property
    def proxy(self) -> str:

        proxy = self._fetch_proxy()
        proxy_list_length = len(self._proxy_list)

        while not proxy.valid:
            self._current_id += 1
            if self._current_id == proxy_list_length - 1:
                raise NoValidProxyError('All of your proxies are invalid')
            proxy = self._fetch_proxy()

        return self._SCHEMA.format(proxy.username,
                                   proxy.password,
                                   proxy.proxy_address,
                                   proxy.port)

    def update(self):
        if self._current_id == len(self._proxy_list) - 1:
            self._current_id = 0
        else:
            self._current_id += 1

