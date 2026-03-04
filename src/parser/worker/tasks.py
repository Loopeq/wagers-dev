from src.parser.worker.app import celery_app
from src.parser.collector.content import collect_content
from src.parser.collector.heads import collect_heads
from src.core.crud.parser.match import archive_and_clear_matches
from src.parser.config import sports
import asyncio

@celery_app.task
def run_collect_heads():
    import asyncio
    asyncio.run(collect_heads(sports=sports))

@celery_app.task
def run_collect_content():
    import asyncio
    asyncio.run(collect_content())

@celery_app.task
def run_archive_matches():
    import asyncio
    asyncio.run(archive_and_clear_matches())