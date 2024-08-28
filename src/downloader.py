import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from straight import save as straight_save


async def download(match_id):
    await straight_save(match_id)


async def run_downloader():
    match_id = 1595892404
    scheduler = AsyncIOScheduler()
    scheduler.add_job(download, 'interval', minutes=5, max_instances=10, args=(match_id, ))

    scheduler.start()

    while True:
        await asyncio.sleep(1)
