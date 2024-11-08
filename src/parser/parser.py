import asyncio
import logging
from datetime import timedelta
from typing import Optional

from src.data.crud import MatchOrm
from src.parser.collector.heads import collect_heads
from src.parser.collector.content import collect_content
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.api.dao.cleanup import CleanUpOrm
from src.parser.collector.history import get_history_details

scheduler = AsyncIOScheduler()


async def cleanup():
    await CleanUpOrm.remove_unref_changes()


async def parse_headers():
    await collect_heads()


async def parse_results():
    await get_history_details(together=5, sleep=0.2)


async def parse_content(start: Optional[int] = None, end: Optional[int] = None):
    stmd = timedelta(hours=start) if start else None
    edmd = timedelta(hours=end) if end else None
    matches = await MatchOrm.get_upcoming_matches(start_timedelta=stmd,
                                                  end_timedelta=edmd)
    await collect_content(matches, start=start, end=end)


async def run_parser():
    await parse_headers()
    await cleanup()
    await parse_results()

    scheduler.add_job(parse_headers, 'interval', minutes=60)
    scheduler.add_job(cleanup, 'interval', days=1)
    scheduler.add_job(parse_results, 'interval', hours=4)
    time_stemps = [
        {'s': 1, "e": 3, "m": 30},
        {'s': 0, "e": 1, "m": 3},
        {'s': 3, "m": 100}]
    for ts in time_stemps:
        scheduler.add_job(parse_content, 'interval', minutes=ts['m'], args=[ts.get('s'), ts.get('e')])
    logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)
    scheduler.start()

