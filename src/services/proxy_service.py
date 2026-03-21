import itertools
import logging
from collections import namedtuple
from pathlib import Path

import requests

from src.settings import settings as conf


logger = logging.getLogger(__name__)


class NoValidProxyError(Exception):
    """Raised when no valid proxies are available."""


Proxy = namedtuple("Proxy", ["username", "password", "proxy_address", "port"])


class ProxyService:
    _SCHEMA = "http://{username}:{password}@{host}:{port}"
    _PROXIES_FILE = Path("storage/proxies.txt")
    _WEBSHARE_URL = "https://proxy.webshare.io/api/v2/proxy/list/"

    _proxy_list: list[Proxy] = []
    _proxy_cycle = None

    @classmethod
    def _fetch_webshare_proxies(cls, timeout: int = 5) -> list[Proxy]:
        headers = {"Authorization": f"Token {conf.WEBSHARE_API}"}

        try:
            response = requests.get(cls._WEBSHARE_URL, headers=headers, timeout=timeout)
            response.raise_for_status()
            results = response.json().get("results", [])

            proxies = []
            for item in results:
                proxies.append(
                    Proxy(
                        username=item["username"],
                        password=item["password"],
                        proxy_address=item["proxy_address"],
                        port=str(item["port"]),
                    )
                )
            return proxies

        except requests.Timeout:
            logger.error("WebShare API did not respond within %s seconds", timeout)
            return []
        except requests.RequestException as exc:
            logger.error("WebShare API request failed: %s", exc)
            return []
        except Exception as exc:
            logger.exception("Unexpected error while fetching proxies: %s", exc)
            return []

    @classmethod
    def _load_file_proxies(cls) -> list[Proxy]:
        if not cls._PROXIES_FILE.exists():
            logger.warning("Proxy file not found: %s", cls._PROXIES_FILE)
            return []

        proxies = []
        try:
            with cls._PROXIES_FILE.open("r", encoding="utf-8") as f:
                for line in f:
                    raw = line.strip()
                    if not raw:
                        continue

                    try:
                        ip, port, username, password = raw.split(":")
                    except ValueError:
                        logger.warning("Invalid proxy line skipped: %s", raw)
                        continue

                    proxies.append(
                        Proxy(
                            username=username,
                            password=password,
                            proxy_address=ip,
                            port=port,
                        )
                    )
        except Exception as exc:
            logger.exception("Failed to read proxy file: %s", exc)
            return []

        return proxies

    @classmethod
    def _ensure_initialized(cls) -> None:
        if cls._proxy_cycle is not None:
            return

        proxies = cls._fetch_webshare_proxies(timeout=10)
        if not proxies:
            proxies = cls._load_file_proxies()

        if not proxies:
            raise NoValidProxyError("No valid proxies available")

        cls._proxy_list = proxies
        cls._proxy_cycle = itertools.cycle(cls._proxy_list)

    @classmethod
    def _get_next_proxy(cls) -> Proxy:
        cls._ensure_initialized()
        return next(cls._proxy_cycle)

    @classmethod
    def get_proxy(cls) -> str:
        proxy = cls._get_next_proxy()
        return cls._SCHEMA.format(
            username=proxy.username,
            password=proxy.password,
            host=proxy.proxy_address,
            port=proxy.port,
        )

    @classmethod
    def get_proxy_object(cls) -> dict:
        proxy = cls._get_next_proxy()
        return {
            "server": f"http://{proxy.proxy_address}:{proxy.port}",
            "username": proxy.username,
            "password": proxy.password,
        }

    @classmethod
    def reload(cls) -> None:
        cls._proxy_list = []
        cls._proxy_cycle = None
        cls._ensure_initialized()