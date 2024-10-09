from src.parser.utils import proxy_manager
import re


def test_proxy_string():
    assert isinstance(proxy_manager.proxy, str)


def test_proxy_valid_pattern():
    pattern = r'http://([^:]+):([^@]+)@([\d.]+):(\d+)'
    assert re.fullmatch(pattern, proxy_manager.proxy)


def test_proxy_update():
    old_proxy = proxy_manager.proxy
    proxy_manager.update()
    new_proxy = proxy_manager.proxy
    assert old_proxy != new_proxy
