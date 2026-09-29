import json
import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from graphtutor.api.v1.auth_deps import get_current_user_v1
from graphtutor.models.user import User
from graphtutor.learning.seed_lessons import SEED_LESSONS
from graphtutor.learning.explainer import AdaptiveExplainer
from graphtutor.schemas.lesson import LessonPayload

router = APIRouter(prefix="/lessons", tags=["Lessons"])


async def sse_event_stream(payload: LessonPayload):
    full_dict = payload.model_dump()

    header_data = {
        "event": "start",
        "concept_slug": payload.concept_slug,
        "display_name": payload.display_name,
        "theme": payload.theme.value,
        "summary": payload.summary,
    }
    yield f"data: {json.dumps(header_data)}\n\n"
    await asyncio.sleep(0.05)

    anchor_data = {
        "event": "section",
        "section": "intuition_anchor",
        "content": payload.intuition_anchor,
    }
    yield f"data: {json.dumps(anchor_data)}\n\n"
    await asyncio.sleep(0.05)

    body_data = {
        "event": "payload",
        "data": full_dict,
    }
    yield f"data: {json.dumps(body_data)}\n\n"
    await asyncio.sleep(0.02)

    yield "data: [DONE]\n\n"


@router.get("/{slug}")
async def get_lesson(
    slug: str,
    stream: Optional[int] = Query(0, description="Set to 1 for Server-Sent Events (SSE) streaming"),
    level: Optional[str] = Query(None, description="Explanation level (beginner, intermediate, advanced)"),
    current_user: User = Depends(get_current_user_v1),
):
    clean_slug = slug.lower().strip()

    if clean_slug in SEED_LESSONS:
        payload = SEED_LESSONS[clean_slug]
    else:
        explainer = AdaptiveExplainer()
        target_level = level or current_user.explanation_level or "intermediate"
        payload = await explainer.generate_lesson_payload(
            concept=clean_slug,
            level=target_level,
        )

    if stream == 1:
        return StreamingResponse(
            sse_event_stream(payload),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    return payload
