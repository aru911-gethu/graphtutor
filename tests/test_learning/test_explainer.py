import pytest
from graphtutor.learning.explainer import AdaptiveExplainer, detect_theme
from graphtutor.schemas.lesson import LearningTheme


def test_theme_detection():
    assert detect_theme("Docker Containers", "DevOps") == LearningTheme.SYSTEMS
    assert detect_theme("Linear Algebra Matrix Multiplication", "Math") == LearningTheme.MATH
    assert detect_theme("Attention Mechanism", "AI-ML") == LearningTheme.AI_PIPELINE
    assert detect_theme("Monolith vs Microservice Trade-offs", "Programming") == LearningTheme.DECISIONS
    assert detect_theme("Python Function Decorators", "Programming") == LearningTheme.CODE


@pytest.mark.asyncio
async def test_adaptive_explainer_fallback_payload():
    explainer = AdaptiveExplainer()
    payload = await explainer.generate_lesson_payload(
        concept="Attention Mechanism",
        level="working",
        known_concepts=["Neural Networks", "Linear Algebra"],
    )

    assert payload.display_name == "Attention Mechanism"
    assert payload.theme == LearningTheme.AI_PIPELINE
    assert payload.summary
    assert payload.intuition_anchor
    assert len(payload.tensor_pipeline_steps) > 0
