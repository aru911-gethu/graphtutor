import pytest
from thinknx.learning.quiz import QuizGenerator


@pytest.mark.asyncio
async def test_quiz_generator():
    """Verify quiz generation returns valid question schema."""
    quiz_gen = QuizGenerator()
    questions = await quiz_gen.generate(
        concept="Knowledge Graphs",
        level="working",
        count=2
    )

    assert len(questions) == 2
    for q in questions:
        assert "question" in q
        assert "options" in q
        assert "correct_answer" in q
        assert len(q["options"]) >= 2


@pytest.mark.asyncio
async def test_quiz_evaluation():
    """Verify answer evaluation returns correct score and FSRS rating."""
    quiz_gen = QuizGenerator()

    # Exact match
    res_correct = await quiz_gen.evaluate_answer(
        question="What is Neo4j?",
        correct_answer="A graph database",
        student_answer="A graph database"
    )
    assert res_correct["correct"] is True
    assert res_correct["fsrs_rating"] == 4

    # Wrong answer
    res_wrong = await quiz_gen.evaluate_answer(
        question="What is Neo4j?",
        correct_answer="A graph database",
        student_answer="A relational SQL engine"
    )
    assert res_wrong["correct"] is False
    assert res_wrong["fsrs_rating"] == 1
