from celery import Celery

from app.config import settings

celery_app = Celery(
    "ai_office",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
celery_app.conf.update(
    worker_prefetch_multiplier=1,
    task_soft_time_limit=600,
    task_time_limit=660,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)


@celery_app.task(name="run_pipeline", bind=True, max_retries=0)
def run_pipeline(self, task_id: str) -> None:
    import asyncio

    from app.pipeline.orchestrator import _run_pipeline_async

    asyncio.run(_run_pipeline_async(task_id))
