import asyncio
from src.core.crud.parser.match import clear_events_by_start_time
from src.parser.config import sports, parse_headers, clear_interval
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.parser.collector.content import collect_content
from src.parser.collector.heads import collect_heads
import src.core.crud.parser.sport as sport
from src.parser.collector.history import save_history
from apscheduler.triggers.cron import CronTrigger


scheduler = AsyncIOScheduler()


async def run_parser():
    await save_history()
    await sport.add_sports(sports=sports)
    await collect_heads(sports=sports)
    await collect_content()
    await clear_events_by_start_time()

    scheduler.add_job(save_history, CronTrigger(hour=1, minute=25))
    scheduler.add_job(collect_heads, 'interval', minutes=parse_headers, args=[sports])
    scheduler.add_job(collect_content, 'interval', minutes=3)
    scheduler.add_job(clear_events_by_start_time, 'interval', days=int(clear_interval))
    scheduler.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(run_parser())
