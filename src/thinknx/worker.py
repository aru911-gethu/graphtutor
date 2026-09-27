from celery import Celery
from thinknx.config import settings

celery_app = Celery(
    "thinknx",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)


@celery_app.task(name="thinknx.worker.ingest_source_task")
def ingest_source_task(user_id: str, source_type: str, payload: dict) -> dict:
    """Background task to ingest text, audio, image, or repo sources."""
    import asyncio
    from thinknx.ingest.router import IngestionRouter

    router = IngestionRouter()

    async def _run():
        return await router.dispatch(user_id=user_id, source_type=source_type, payload=payload)

    return asyncio.run(_run())


@celery_app.task(name="thinknx.worker.poll_feeds_task")
def poll_feeds_task(feed_url: str) -> dict:
    """Periodic task to poll RSS/feed updates for new concepts."""
    import asyncio
    from thinknx.ingest.feeds import FeedIngestor

    ingestor = FeedIngestor()

    async def _run():
        return await ingestor.fetch_and_extract(feed_url)

    return asyncio.run(_run())
