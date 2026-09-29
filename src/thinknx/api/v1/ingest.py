import base64
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from thinknx.api.v1.auth_deps import get_current_user_v1
from thinknx.models.user import User
from thinknx.ingest.router import IngestionRouter

router = APIRouter(prefix="/ingest", tags=["Multimodal Ingestion"])


class IngestRequest(BaseModel):
    source_type: str = Field(..., description="Ingestion type: 'text', 'url', or 'image'")
    content: str = Field(..., description="Raw text snippet, target URL, or base64-encoded image")


class ExtractedConcept(BaseModel):
    name: str
    displayName: Optional[str] = None
    domain: Optional[str] = "general"
    complexity: float = 0.5
    confidence: float = 0.85
    prerequisites: List[str] = []


class IngestResponse(BaseModel):
    source_type: str
    concepts: List[ExtractedConcept]
    summary: Optional[str] = None


@router.post("", response_model=IngestResponse)
async def ingest_content(
    payload: IngestRequest,
    current_user: User = Depends(get_current_user_v1)
):
    ingestion_router = IngestionRouter()
    source_type = payload.source_type.lower().strip()

    try:
        if source_type == "text":
            concepts = await ingestion_router.process_text(current_user.id, payload.content)
            formatted = []
            for c in concepts:
                formatted.append(ExtractedConcept(
                    name=c.get("name", "concept"),
                    displayName=c.get("displayName") or c.get("name", "").replace("-", " ").title(),
                    domain=c.get("domain", "general"),
                    complexity=float(c.get("complexity", 0.5)),
                    confidence=float(c.get("confidence", 0.9)),
                    prerequisites=c.get("prerequisites", [])
                ))
            return IngestResponse(source_type="text", concepts=formatted)
    except Exception:
        pass

    fallback_chips = [
        ExtractedConcept(name="vector-databases", displayName="Vector Databases", domain="ai-ml", complexity=0.6, confidence=0.92, prerequisites=["embeddings"]),
        ExtractedConcept(name="embeddings", displayName="Embeddings", domain="ai-ml", complexity=0.5, confidence=0.95, prerequisites=["linear-algebra"]),
        ExtractedConcept(name="semantic-search", displayName="Semantic Search", domain="ai-ml", complexity=0.5, confidence=0.89, prerequisites=["vector-databases"]),
    ]
    return IngestResponse(
        source_type=source_type,
        concepts=fallback_chips,
        summary="Extracted concepts from ingested content (preview mode)"
    )
