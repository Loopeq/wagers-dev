from src.proxy import proxy_manager
import re


def test_proxy_string():
    assert isinstance(proxy_manager.proxy, str)


def test_proxy_valid_pattern():
    pattern = r'http://([^:]+):([^@]+)@([\d.]+):(\d+)'
    assert re.fullmatch(pattern, proxy_manager.proxy)

