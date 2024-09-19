import datetime
import pytz
import json
from pathlib import Path


def iso_to_utc(iso_str: str):
    return datetime.datetime.fromisoformat(iso_str.replace("Z", ""))


def gmt_to_utc(gmt_str: str):
    return datetime.datetime.strptime(gmt_str, '%a, %d %b %Y %H:%M:%S GMT').replace(tzinfo=None)


def utc_to_msc(utc_data: str):
    msc_zone = pytz.timezone('Europe/Moscow')
    msc_time = utc_data.astimezone(msc_zone)
    return msc_time


def calc_coeff(price):
    if price > 0:
        return round(price / 100 + 1, 3)
    return round(abs(100 / price) + 1, 3)


def period_corrector(title: str, period: int) -> str:
    if period == 0:
        prefix = 'Игра'
    else:
        prefix = f'{period} Тайм'
    total = f'{title.title()} - {prefix}'
    return total
