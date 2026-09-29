import pytest
from graphtutor.learning.mastery import FSRSMastery
from tests.conftest import MockNeo4jSession


def test_fsrs_new_card():
    """Verify initial card parameters."""
    mastery = FSRSMastery()
    card = mastery.new_card()
    assert card["retrievability"] == 1.0
    assert card["stability"] > 0
    assert card["depth"] == "surface"


def test_fsrs_review_updates():
    """Verify review updates for Again (1) vs Easy (4)."""
    mastery = FSRSMastery()
    initial = mastery.new_card()

    # Again review (failed)
    res_again = mastery.review(initial, rating=1)
    # Easy review (successful)
    res_easy = mastery.review(initial, rating=4)

    assert res_easy["mastery"] > res_again["mastery"]
    assert res_easy["stability"] > res_again["stability"]


@pytest.mark.asyncio
async def test_fsrs_record_review():
    """Verify record review integration with Neo4j session."""
    mastery = FSRSMastery()
    session = MockNeo4jSession()

    res = await mastery.record_review(
        session=session,
        user_id="telegram:12345",
        concept_name="transformers",
        rating=3
    )

    assert "mastery" in res
    assert "stability" in res
    assert "depth" in res
    assert len(session.ran_queries) >= 1
