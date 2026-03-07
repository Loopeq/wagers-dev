from src.parser.worker.app import celery_app
from src.parser.collector.content import collect_content
from src.parser.collector.heads import collect_heads
from src.core.crud.parser.match import archive_and_clear_matches
from src.parser.config import sports
import asyncio


@celery_app.task(
    name="run_collect_heads",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_collect_heads(self):
    asyncio.run(collect_heads(sports=sports))


@celery_app.task(
    name="run_collect_content",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_collect_content(self):
    asyncio.run(collect_content())


@celery_app.task(
    name="run_archive_matches",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_archive_matches(self):
    asyncio.run(archive_and_clear_matches())
