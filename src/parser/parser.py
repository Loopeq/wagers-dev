import asyncio
from src.core.crud.parser.match import archive_and_clear_matches
from src.parser.config import sports, parse_headers, clear_interval
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.parser.collector.content import collect_content
from src.parser.collector.heads import collect_heads
import src.core.crud.parser.sport as sport
from src.core.crud.api.related import get_sport_id_by_match_id
from src.core.db.db_helper import db_helper

scheduler = AsyncIOScheduler()

async def collect_heads_wrapper(sports):
    await collect_heads(sports=sports)



async def run_parser():
    await sport.add_sports(sports=sports)
    await collect_heads_wrapper(sports=sports)
    await collect_content()
    await archive_and_clear_matches()

    scheduler.add_job(collect_heads_wrapper, 'interval', minutes=parse_headers, args=[sports])
    scheduler.add_job(collect_content, 'interval', minutes=3)
    scheduler.add_job(archive_and_clear_matches, 'interval', days=int(clear_interval))
    scheduler.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(run_parser())
