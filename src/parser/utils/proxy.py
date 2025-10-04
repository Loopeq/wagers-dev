import itertools
import logging
from collections import namedtuple
from src.core.settings import settings as conf
import requests

class NoValidProxyError(Exception):
    """When all proxies are invalid"""
    pass

Proxy = namedtuple("Proxy", ["username", "password", "proxy_address", "port"])


class ProxyManager:
    # (0) username (1) password (2) ip (3) port
    _SCHEMA = 'http://{0}:{1}@{2}:{3}'

    def __init__(self):
        self._proxy_list = self._get_proxies(10)
        if not len(self._proxy_list):
            with open('data/proxies.txt') as f: 
                for pr in f.readlines(): 
                    pr_strip = pr.rstrip('\n')
                    ip, port, username, password = pr_strip.split(':')
                    proxy = Proxy(username, password, ip, port)
                    self._proxy_list.append(proxy)                    

        self._proxy_cycle = itertools.cycle(self._proxy_list)
        self._current_proxy = next(self._proxy_cycle)


    @staticmethod
    def _get_proxies(timeout=5):
        url = "https://proxy.webshare.io/api/v2/proxy/list/"
        headers = {"Authorization": f"Token {conf.WEBSHARE_API}"}
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            return resp.json().get("results", [])
        except requests.Timeout:
            logging.error(f"WebShare API did not respond within {timeout} seconds")
            return []

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