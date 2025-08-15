import itertools
import logging

from webshare import ApiClient
from src.core.settings import settings as conf


class NoValidProxyError(Exception):
    """When all proxies are invalid"""
    pass


class ProxyManager:
    # (0) username (1) password (2) ip (3) port
    _SCHEMA = 'http://{0}:{1}@{2}:{3}'

    def __init__(self):
        self._client = ApiClient(conf.WEBSHARE_API)
        self._proxy_list = self._client.get_proxy_list().get_results()

        if not self._proxy_list:
            logging.error("No proxies available from WebShare API")

        self._proxy_cycle = itertools.cycle(self._proxy_list)
        self._current_proxy = next(self._proxy_cycle)

    @property
    def proxy(self) -> str:
        proxy = next(self._proxy_cycle)
        return self._SCHEMA.format(proxy.username, proxy.password, proxy.proxy_address, proxy.port)

    @property
    def proxy_object(self) -> dict:
        proxy = next(self._proxy_cycle)
        return {
            'server': f'http://{proxy.proxy_address}:{proxy.port}',
            'username': proxy.username,
            'password': proxy.password,
        }
