from celery import Celery
from src.core.settings import settings
import src.parser.worker.startup  # noqa: F401

celery_app = Celery(
    "spredly_parser",
    broker=f"{settings.REDIS_URL}/0",
    backend=f"{settings.REDIS_URL}/1",
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

celery_app.autodiscover_tasks(["src.parser.worker"])
