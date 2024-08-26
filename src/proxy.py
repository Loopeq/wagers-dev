from webshare import ApiClient
from webshare.util import Proxy

from settings import settings as conf
from dataclasses import dataclass


@dataclass
class ProxyModel:
    data: list[Proxy]
    count: int


class InvalidProxy(Exception):
    """Plug"""
    pass


class ProxyManager:
    SCHEMA = 'http://{0}:{1}@{2}:{3}'

    def __init__(self):
        self.current = None
        self._current_id = 0
        self._client = ApiClient(conf.WEBSHARE_API)
        self.proxies: ProxyModel = self._get_proxy_list()
        self.update()

    def _get_proxy_list(self):
        response = self._client.get_proxy_list()
        proxies = response.get_results()
        count = response.count
        return ProxyModel(proxies, count)

    def _fetch_proxy(self) -> str | None:
        # (0) username (1) password (2) ip (3) port
        if self._current_id < self.proxies.count:
            proxy = self.proxies.data[self._current_id]
            if proxy.valid:
                return self.SCHEMA.format(proxy.username,
                                          proxy.password,
                                          proxy.proxy_address,
                                          proxy.port)
            raise InvalidProxy(f'{proxy.__dict__} - is invalid')
        raise IndexError('_current_id out of range')

    def update(self):
        while True:
            try:
                self._current_id += 1
                self.current = self._fetch_proxy()
                break
            except InvalidProxy as e:
                print(e)
                self._current_id += 1
                self.current = self._fetch_proxy()
            except IndexError as e:
                print(e)
                self._current_id = 0



