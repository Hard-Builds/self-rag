from celery import Celery
from kombu import Queue

from app.core.config import settings

celery_app = Celery(
    "self-rag-worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.worker.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    worker_pool="celery_aio_pool.pool:AsyncIOPool",
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
    task_queues=[Queue("ingest")],
    task_default_queue="ingest",
    task_annotations={"app.worker.tasks.ingest_document": {"rate_limit": "10/m"}},
    task_soft_time_limit=3600,
    task_time_limit=4200,
)
