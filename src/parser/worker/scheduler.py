from celery.schedules import crontab
from src.parser.worker.app import celery_app

celery_app.conf.beat_schedule = {
    "collect-heads-every-3-min": {
        "task": "run_collect_heads",
        "schedule": crontab(minute="*/3"),
        "options": {"expires": 120},
    },
    "collect-content-every-3-min": {
        "task": "run_collect_content",
        "schedule": crontab(minute="*/3"),
        "options": {"expires": 120},
    },
    "archive-matches-daily": {
        "task": "run_archive_matches",
        "schedule": crontab(hour=2, minute=0),
        "options": {"expires": 3600},
    },
}
