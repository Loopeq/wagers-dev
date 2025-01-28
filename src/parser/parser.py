import asyncio
from datetime import timedelta
from typing import Optional
from src.core.crud.parser import MatchOrm
from src.core.parser.collector.heads import collect_heads
from src.core.parser.collector.content import collect_content
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.core.crud.api.cleanup import CleanUpOrm
from src.core.parser.collector.history import get_history_details

scheduler = AsyncIOScheduler()


async def cleanup_matches():
    await CleanUpOrm.remove_unref_matches()


async def cleanup_changes():
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

    scheduler.add_job(parse_headers, 'interval', minutes=60)
    scheduler.add_job(cleanup_changes, 'interval', days=5)
    scheduler.add_job(parse_results, 'interval', days=1)
    scheduler.add_job(cleanup_matches, 'interval', days=20)
    time_stemps = [
        {'s': 1, "e": 3, "m": 30},
        {'s': 0, "e": 1, "m": 3},
        {'s': 3, "m": 100}]
    for ts in time_stemps:
        scheduler.add_job(
            parse_content,
            'interval',
            args=[ts.get('s'), ts.get('e')],
            minutes=ts['m'],
        )
    scheduler.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(run_parser())
