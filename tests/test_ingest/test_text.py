import pytest
from thinknx.ingest.text import TextIngestor


@pytest.mark.asyncio
async def test_text_ingestor_rule_fallback():
    """Verify concept extraction finds key technical terms."""
    ingestor = TextIngestor()
    text = "Today I learned about transformers, attention mechanism, and docker containers."
    concepts = await ingestor.extract_concepts(text)

    assert len(concepts) >= 2
    names = [c["name"] for c in concepts]
    assert "transformers" in names
    assert "attention-mechanism" in names or "docker" in names
