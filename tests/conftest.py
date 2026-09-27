import pytest
import pytest_asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import AsyncClient, ASGITransport

from thinknx.database import Base, get_db
from thinknx.main import app


# In-memory test SQLite engine
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a fresh isolated in-memory SQLite database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Test client configured with overridden async database dependency."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


class MockNeo4jRecord(dict):
    """Dict-like mock Neo4j record supporting item access."""
    def __getitem__(self, key):
        return super().get(key)


class MockNeo4jResult:
    """Mock query result yielding records and supporting single() and data()."""
    def __init__(self, data=None):
        self._data = data or []

    async def single(self):
        return MockNeo4jRecord(self._data[0]) if self._data else None

    async def data(self):
        return self._data

    def __aiter__(self):
        self._iter = iter(self._data)
        return self

    async def __anext__(self):
        try:
            return MockNeo4jRecord(next(self._iter))
        except StopIteration:
            raise StopAsyncIteration


class MockNeo4jSession:
    """Simulates an active Neo4j async session for unit testing."""
    def __init__(self):
        self.ran_queries = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def run(self, query: str, **params):
        self.ran_queries.append((query, params))

        q_lower = query.lower()
        if "return 1 as ok" in q_lower:
            return MockNeo4jResult([{"ok": 1}])
        elif "count(c) as totalconcepts" in q_lower:
            return MockNeo4jResult([{
                "totalConcepts": 12,
                "mastered": 5,
                "inProgress": 4,
                "gaps": 3,
                "reviewsThisWeek": 8
            }])
        elif "match (c:concept {name: $name})" in q_lower:
            return MockNeo4jResult([{
                "concept": {
                    "name": params.get("name", "transformers"),
                    "displayName": params.get("displayName", "Transformers"),
                    "domain": "ai-ml",
                    "complexity": 0.7
                }
            }])
        elif "match (u:user {userid: $userid})-[k:knows]->(c:concept)" in q_lower:
            return MockNeo4jResult([
                {
                    "concept": "linear-algebra",
                    "displayName": "Linear Algebra",
                    "domain": "math",
                    "mastery": 0.85,
                    "stability": 30.0,
                    "difficulty": 0.2,
                    "retrievability": 0.95,
                    "depth": "deep",
                    "lastReview": "2026-03-20T10:00:00Z"
                },
                {
                    "concept": "transformers",
                    "displayName": "Transformers",
                    "domain": "ai-ml",
                    "mastery": 0.4,
                    "stability": 2.0,
                    "difficulty": 0.5,
                    "retrievability": 0.72,
                    "depth": "surface",
                    "lastReview": "2026-03-25T14:30:00Z"
                }
            ])
        elif "get_next_topics" in q_lower or "prereq in masteredlist" in q_lower:
            return MockNeo4jResult([
                {"concept": "attention-mechanism", "displayName": "Attention Mechanism", "domain": "ai-ml", "complexity": 0.7}
            ])
        elif "get_learning_path" in q_lower or "[:requires*0..]" in q_lower:
            return MockNeo4jResult([
                {"concept": "linear-algebra", "displayName": "Linear Algebra", "complexity": 0.4, "depth": 2},
                {"concept": "deep-learning", "displayName": "Deep Learning", "complexity": 0.6, "depth": 1},
                {"concept": "transformers", "displayName": "Transformers", "complexity": 0.7, "depth": 0},
            ])

        return MockNeo4jResult([{"success": True}])


@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j AsyncDriver returning simulated session."""
    driver = MagicMock()
    session = MockNeo4jSession()
    driver.session.return_value = session
    return driver
