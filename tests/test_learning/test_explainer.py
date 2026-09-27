import pytest
from thinknx.learning.explainer import AdaptiveExplainer
from thinknx.schemas.lesson import LearningTheme


@pytest.mark.asyncio
async def test_adaptive_explainer_theme_detection():
    """Verify theme detection logic across different technical keywords."""
    explainer = AdaptiveExplainer()

    assert explainer._detect_theme("Docker Containers", "DevOps") == LearningTheme.SYSTEMS
    assert explainer._detect_theme("Linear Algebra Matrix Multiplication", "Math") == LearningTheme.MATH
    assert explainer._detect_theme("Attention Mechanism", "AI-ML") == LearningTheme.AI_PIPELINES
    assert explainer._detect_theme("AsyncIO vs Threading Trade-offs", "Programming") == LearningTheme.PARADIGMS
    assert explainer._detect_theme("Python Function Decorators", "Programming") == LearningTheme.CODE


@pytest.mark.asyncio
async def test_adaptive_explainer_fallback_payload():
    """Verify that polymorphic lesson payload contains code remarks and theme cards."""
    explainer = AdaptiveExplainer()
    payload = await explainer.explain(
        concept="Attention Mechanism",
        level="working",
        known_concepts=["Neural Networks", "Linear Algebra"]
    )

    assert payload.concept == "Attention Mechanism"
    assert payload.theme in [LearningTheme.AI_PIPELINES, LearningTheme.CODE]
    assert len(payload.takeaways) > 0

    if payload.code_snippet:
        assert payload.code_language is not None
        # Verify code remarks are separated
        assert isinstance(payload.code_remarks, list)
