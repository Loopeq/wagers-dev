import asyncio
from datetime import timedelta
from typing import Optional

from src.data.crud import create_tables, MatchOrm
from src.parser.collector.heads import collect_heads
from src.parser.collector.content import collect_content

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.logs import logger


scheduler = AsyncIOScheduler()


async def parse(start: Optional[int] = None, end: Optional[int] = None):
    logger.info(f'Start collecting data between {start} and {end}')
    stmd = timedelta(hours=start) if start else None
    edmd = timedelta(hours=end) if end else None
    await collect_heads()
    matches = await MatchOrm.get_upcoming_matches(start_timedelta=stmd,
                                                  end_timedelta=edmd)
    point_delay = 2 if start in [1, 3] else 0
    await collect_content(matches, point_delay=point_delay)
    logger.info(f'Finish collecting data between {start} and {end}')


async def run_parser():
    time_stemps = [
                   {'s': 1, "e": 3, "m": 300},
                   {'s': 0, "e": 1, "m": 300},
                   {'s': 3, "m": 20}]
    for ts in time_stemps:
        scheduler.add_job(parse, 'interval', seconds=ts['m'], args=[ts.get('s'), ts.get('e')])
    scheduler.start()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(run_parser())
    loop.run_forever()
