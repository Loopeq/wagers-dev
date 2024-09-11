import datetime
import pytz
import json
from pathlib import Path


def iso_to_msc(iso_date: str):
    from_iso = datetime.datetime.fromisoformat(iso_date[:-1])
    utc_zone = pytz.utc
    msc_zone = pytz.timezone('Europe/Moscow')

    from_iso = utc_zone.localize(from_iso)
    msc_time = from_iso.astimezone(msc_zone)
    return str(msc_time)[:-6]


def gmt_to_msc(gmt_date: str):
    date_format = "%a, %d %b %Y %H:%M:%S %Z"

    gmt_time = datetime.datetime.strptime(gmt_date, date_format)

    utc_zone = pytz.utc
    gmt_time = utc_zone.localize(gmt_time)

    msc_zone = pytz.timezone("Europe/Moscow")
    msc_time = gmt_time.astimezone(msc_zone)

    return str(msc_time)[:-6]


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
