import pytest
from unittest.mock import MagicMock
from thinknx.learning.engine import LearningEngine
from tests.conftest import MockNeo4jSession


@pytest.mark.asyncio
async def test_learning_engine_teach_loop(mock_neo4j_driver):
    """Verify full teaching loop returns concept, lesson payload, and quiz."""
    engine = LearningEngine(driver=mock_neo4j_driver)

    result = await engine.teach(user_id="telegram:55555", topic="Transformers")
    assert "concept" in result
    assert "payload" in result
    assert "chat_markdown" in result
    assert "quiz" in result
    assert result["payload"].display_name == "Transformers"


@pytest.mark.asyncio
async def test_learning_engine_evaluate_answer(mock_neo4j_driver):
    """Verify evaluation and review update in learning engine."""
    engine = LearningEngine(driver=mock_neo4j_driver)

    eval_res = await engine.evaluate_answer(
        user_id="telegram:55555",
        concept_name="transformers",
        question="What powers Transformers?",
        correct_answer="Self-attention mechanism",
        student_answer="Self-attention mechanism"
    )

    assert eval_res["correct"] is True
    assert "mastery" in eval_res
    assert "depth" in eval_res
