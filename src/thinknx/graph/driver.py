from typing import Optional
from neo4j import AsyncGraphDatabase, AsyncDriver
import structlog

from thinknx.config import settings

logger = structlog.get_logger(__name__)

_driver: Optional[AsyncDriver] = None


def get_driver() -> AsyncDriver:
    """Get or initialize the global Neo4j async driver singleton."""
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
            connection_acquisition_timeout=30.0,
        )
    return _driver


async def close_driver() -> None:
    """Close the Neo4j driver connection pool."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None
        logger.info("Neo4j driver connection pool closed.")


async def health_check() -> bool:
    """Verify connectivity to Neo4j instance."""
    try:
        driver = get_driver()
        async with driver.session() as session:
            result = await session.run("RETURN 1 AS ok")
            record = await result.single()
            return bool(record and record["ok"] == 1)
    except Exception as e:
        logger.warning("Neo4j health check failed", error=str(e))
        return False
