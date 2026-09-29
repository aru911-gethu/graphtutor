import pytest
from unittest.mock import MagicMock
import graphtutor.graph.queries as queries
from tests.conftest import MockNeo4jSession


@pytest.mark.asyncio
async def test_create_user_query():
    """Verify user creation query parameterization."""
    session = MockNeo4jSession()
    user = await queries.create_user(session, user_id="telegram:987654", name="Alice", platform="telegram")
    assert len(session.ran_queries) == 1
    query, params = session.ran_queries[0]
    assert "MERGE (u:User {userId: $userId})" in query
    assert params["userId"] == "telegram:987654"
    assert params["name"] == "Alice"


@pytest.mark.asyncio
async def test_get_user_concepts():
    """Verify user concept retrieval and isolation."""
    session = MockNeo4jSession()
    concepts = await queries.get_user_concepts(session, user_id="telegram:987654")
    assert len(concepts) == 2
    assert concepts[0]["concept"] == "linear-algebra"
    assert concepts[1]["concept"] == "transformers"


@pytest.mark.asyncio
async def test_propagate_failure_query():
    """Verify failure propagation query execution."""
    session = MockNeo4jSession()
    await queries.propagate_failure(session, user_id="telegram:987654", failed_concept="linear-algebra", decay_factor=0.75)
    assert len(session.ran_queries) == 1
    query, params = session.ran_queries[0]
    assert "[:REQUIRES]" in query
    assert params["failedConcept"] == "linear-algebra"
    assert params["decayFactor"] == 0.75
