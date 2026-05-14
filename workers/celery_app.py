import ssl
from celery import Celery
from core.config import settings

celery_app = Celery(
    "website_analyzer",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["workers.tasks"],
)

# Upstash uses rediss:// (TLS) — requires explicit SSL config in Celery
_ssl = {"ssl_cert_reqs": ssl.CERT_NONE}

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_use_ssl=_ssl,
    redis_backend_use_ssl=_ssl,
)
