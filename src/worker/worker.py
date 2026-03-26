from arq import cron
from arq.connections import RedisSettings
from src.worker.tasks import startup, get_heads, get_straight, archive_matches
from src.settings import settings


class WorkerSettings:
    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        database=0,
    )

    functions = [startup, get_heads, get_straight, archive_matches]

    cron_jobs = [
        cron(get_heads, minute=list(range(0, 60, 1)), max_tries=5),
        cron(get_straight, minute=list(range(0, 60, 1)), max_tries=5),
        cron(archive_matches, hour=2, minute=0, max_tries=5),
    ]

    on_startup = startup
