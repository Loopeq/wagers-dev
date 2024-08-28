from webshare import ApiClient

from src.settings import settings as conf


class NoValidProxyError(Exception):
    """Plug"""
    pass


class ProxyManager:
    # (0) username (1) password (2) ip (3) port
    _SCHEMA = 'http://{0}:{1}@{2}:{3}'
    _CLIENT = ApiClient(conf.WEBSHARE_API)

    def __init__(self):
        self._proxy_list = self._CLIENT.get_proxy_list().get_results()
        self._current_id = 0

    def _fetch_proxy(self):
        return self._proxy_list[self._current_id]

    @property
    def proxy(self) -> str:

        proxy = self._fetch_proxy()
        proxy_list_length = len(self._proxy_list)

        while not proxy.valid:
            self._current_id += 1
            if self._current_id >= proxy_list_length - 1:
                raise NoValidProxyError('All of your proxies are invalid')
            proxy = self._fetch_proxy()

        return self._SCHEMA.format(proxy.username,
                                   proxy.password,
                                   proxy.proxy_address,
                                   proxy.port)

    def update(self):
        if self._current_id == len(self._proxy_list)-1:
            self._current_id = 0
        else:
            self._current_id += 1


proxy_manager = ProxyManager()
