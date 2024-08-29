import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler


async def download():
    pass


async def run_downloader(hours: int = 1):
    scheduler = AsyncIOScheduler()

    scheduler.add_job(download, 'interval', minutes=hours)
    scheduler.start()

    while True:
        await asyncio.sleep(1)
