import asyncio
from src.core.crud.parser.match import clear_events_by_start_time, get_upcoming_matches
from src.parser.config import sports, parse_headers, clear_interval
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.parser.collector.content import collect_content
from src.parser.collector.heads import collect_heads
import src.core.crud.parser.sport as sport
from src.core.crud.api.related import get_sport_id_by_match_id
from src.core.db.db_helper import db_helper

scheduler = AsyncIOScheduler()

'''
def schedule_match_callback(match):
    run_time = match.start_time - timedelta(minutes=10)
    scheduler.add_job(
        send_report,
        "date",
        replace_existing=True,
        run_date=run_time,
        args=[match.id],
        id=f"{match.id}"
    )
'''

'''
async def reschedule_all_matches():
    matches = await get_upcoming_matches(sport_id=33, include_parents=False)
    for match in matches:
        schedule_match_callback(match)
'''

async def collect_heads_wrapper(sports):
    results = await collect_heads(sports=sports)
    async with db_helper.session_factory() as session:
        for match in results:
            sport_id = await get_sport_id_by_match_id(match_id=match.id, session=session)
            if sport_id != 33: # Убираем всё кроме тенниса
                continue
            if match.parent_id is not None:
                continue
            # schedule_match_callback(match=match)


async def run_parser():
    await sport.add_sports(sports=sports)
    await collect_heads_wrapper(sports=sports)
    await collect_content()
    await clear_events_by_start_time()
    # await reschedule_all_matches()

    scheduler.add_job(collect_heads_wrapper, 'interval', minutes=parse_headers, args=[sports])
    scheduler.add_job(collect_content, 'interval', minutes=3)
    scheduler.add_job(clear_events_by_start_time, 'interval', days=int(clear_interval))
    scheduler.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(run_parser())
