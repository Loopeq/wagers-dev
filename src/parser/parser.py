import asyncio
import logging

from src.core.crud.parser.match import clear_events_by_start_time
from src.parser.config import sports, parse_headers, clear_interval
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.parser.collector.content import collect_content
from src.parser.collector.heads import collect_heads
import src.core.crud.parser.sport as sport

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

scheduler = AsyncIOScheduler()


async def run_parser():
    await sport.add_sports(sports=sports)
    await collect_heads(sports=sports)
    await collect_content()
    await clear_events_by_start_time()
    scheduler.add_job(collect_heads, 'interval', minutes=parse_headers, args=[sports])
    scheduler.add_job(collect_content, 'interval', minutes=3)
    scheduler.add_job(clear_events_by_start_time, 'interval', days=int(clear_interval))
    scheduler.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_parser())
