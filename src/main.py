import asyncio
from datetime import timedelta
from threading import Thread

from src.data.crud import create_tables, MatchOrm
from src.collector.heads import collect_heads
from src.collector.content import collect_content

from apscheduler.schedulers.asyncio import AsyncIOScheduler


scheduler = AsyncIOScheduler()


async def collect_one_hour():
    matches = await MatchOrm.get_upcoming_matches(
        start_timedelta=timedelta(hours=1), end_timedelta=timedelta(hours=3)
    )
    await collect_content(matches)


async def collect_two_hour():
    matches = await MatchOrm.get_upcoming_matches(
        start_timedelta=timedelta(minutes=0), end_timedelta=timedelta(hours=1)
    )
    await collect_content(matches)


async def collect_above_three_hour():
    matches = await MatchOrm.get_upcoming_matches(start_timedelta=timedelta(hours=3))
    await collect_content(matches)


async def main():
    await create_tables()
    scheduler.add_job(collect_one_hour, 'interval', minutes=30)
    scheduler.add_job(collect_two_hour, 'interval', minutes=15)
    scheduler.add_job(collect_above_three_hour, 'interval', minutes=60)
    scheduler.start()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.create_task(main())
    loop.run_forever()

