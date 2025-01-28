import asyncio
from src.parser.config import sports, parse_content, parse_allow_types, parse_headers

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.parser.collector.content import collect_content
from src.parser.collector.heads import collect_heads
from src.parser.collector.history import get_history_details
import src.core.crud.parser.sport as sport

scheduler = AsyncIOScheduler()


async def parse_results():
    await get_history_details(together=5, sleep=0.2)


async def run_parser():
    await sport.add_sports(sports=sports)
    await collect_heads(sports=sports)

    scheduler.add_job(collect_heads, 'interval', minutes=parse_headers, args=[sports])
    # scheduler.add_job(parse_results, 'interval', minutes=settings.PARSE_RESULT_M)

    for ts in parse_content:
        scheduler.add_job(
            collect_content,
            'interval',
            args=[ts['start'], ts.get('end'), parse_allow_types],
            minutes=ts['minutes'],
        )

    scheduler.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(run_parser())
