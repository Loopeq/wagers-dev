import asyncio
from datetime import timedelta
from typing import Optional

from src.data.crud import create_tables, MatchOrm
from src.parser.collector.heads import collect_heads
from src.parser.collector.content import collect_content

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.logs import logger
import logging

scheduler = AsyncIOScheduler()


async def parse_headers():
    await collect_heads()


async def parse_content(start: Optional[int] = None, end: Optional[int] = None):
    stmd = timedelta(hours=start) if start else None
    edmd = timedelta(hours=end) if end else None
    matches = await MatchOrm.get_upcoming_matches(start_timedelta=stmd,
                                                  end_timedelta=edmd)
    await collect_content(matches)


async def run_parser():
    await parse_headers()
    scheduler.add_job(parse_headers, 'interval', minutes=60)
    time_stemps = [
        {'s': 1, "e": 3, "m": 30},
        {'s': 0, "e": 1, "m": 5},
        {'s': 3, "m": 100}]

    for ts in time_stemps:
        scheduler.add_job(parse_content, 'interval', minutes=ts['m'], args=[ts.get('s'), ts.get('e')])
    logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
    scheduler.start()

