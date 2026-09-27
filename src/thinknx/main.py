from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uvicorn
import redis.asyncio as aioredis

from thinknx.config import settings
from thinknx.database import init_db
from thinknx.graph.driver import get_driver, close_driver, health_check as neo4j_health_check
from thinknx.graph.schema import init_schema
from thinknx.api.router import api_router
from thinknx.api.lesson import router as lesson_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager:
    Initializes runtime directories, relational database, and Neo4j schema & seed DAG.
    Closes database connections on shutdown.
    """
    settings.ensure_runtime_dirs()
    await init_db()

    # Attempt to initialize Neo4j schema & seed DAG
    try:
        driver = get_driver()
        await init_schema(driver)
        logger.info("Neo4j schema and seed concepts initialized successfully.")
    except Exception as e:
        logger.warning(f"Neo4j initialization skipped on startup ({e}). App running in degraded/dev mode.")

    yield

    # Clean shutdown
    await close_driver()


app = FastAPI(
    title=settings.app_name,
    description="Personal Adaptive Learning Agent delivered via Telegram, Neo4j, and FSRS Spaced Repetition",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Central API Router and WebApp Lesson Router
app.include_router(api_router)
app.include_router(lesson_router)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to OpenAPI interactive documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    """Health check endpoint checking application status, Neo4j, and Redis connectivity."""
    neo4j_ok = await neo4j_health_check()

    redis_ok = False
    try:
        r = aioredis.from_url(settings.redis_url)
        redis_ok = await r.ping()
        await r.close()
    except Exception:
        redis_ok = False

    overall_status = "ok" if (neo4j_ok and redis_ok) else "healthy"

    return {
        "status": overall_status,
        "app": settings.app_name,
        "environment": settings.environment,
        "version": "0.1.0",
        "neo4j": "connected" if neo4j_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
    }


def cli():
    """Command-line entry point to run uvicorn server."""
    uvicorn.run("thinknx.main:app", host="0.0.0.0", port=8000, reload=settings.debug)


if __name__ == "__main__":
    cli()
