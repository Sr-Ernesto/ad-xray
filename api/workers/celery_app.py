from celery import Celery
from api.config import settings

celery_app = Celery(
    "ad_xray",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "api.workers.harvester",
        "api.workers.inspector",
        "api.workers.downloader"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "api.workers.harvester.*": {"queue": "harvester"},
        "api.workers.inspector.*": {"queue": "inspector"},
        "api.workers.downloader.*": {"queue": "downloader"},
    }
)
