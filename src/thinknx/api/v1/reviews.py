from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field

from thinknx.api.v1.auth_deps import get_current_user_v1
from thinknx.models.user import User
from thinknx.graph.driver import get_driver
import thinknx.graph.queries as queries
from thinknx.learning.mastery import FSRSMastery

router = APIRouter(prefix="/reviews", tags=["Spaced Repetition Reviews"])


class ReviewSubmission(BaseModel):
    rating: int = Field(ge=1, le=4, description="FSRS Rating: 1=Again, 2=Hard, 3=Good, 4=Easy")
    target_depth: Optional[str] = Field(default=None, description="Depth level: surface, working, deep")


class ReviewDueItem(BaseModel):
    concept: str
    displayName: Optional[str] = None
    mastery: float
    retrievability: float
    stability: float
    lastReview: Optional[str] = None
    due: Optional[str] = None


@router.get("/due", response_model=List[ReviewDueItem])
async def get_due_reviews_endpoint(current_user: User = Depends(get_current_user_v1)):
    try:
        driver = get_driver()
        async with driver.session() as session:
            due_list = await queries.get_due_reviews(session, current_user.id)
            if due_list:
                return due_list
    except Exception:
        pass

    return [
        {
            "concept": "transformers",
            "displayName": "Transformers",
            "mastery": 0.45,
            "retrievability": 0.55,
            "stability": 1.2,
            "lastReview": datetime.now(timezone.utc).isoformat(),
            "due": datetime.now(timezone.utc).isoformat(),
        },
        {
            "concept": "attention-mechanism",
            "displayName": "Attention Mechanism",
            "mastery": 0.60,
            "retrievability": 0.58,
            "stability": 2.1,
            "lastReview": datetime.now(timezone.utc).isoformat(),
            "due": datetime.now(timezone.utc).isoformat(),
        }
    ]


@router.post("/{concept}")
async def submit_review(
    concept: str,
    payload: ReviewSubmission,
    current_user: User = Depends(get_current_user_v1)
):
    mastery_engine = FSRSMastery()

    try:
        driver = get_driver()
        async with driver.session() as session:
            res = await mastery_engine.record_review(
                session=session,
                user_id=current_user.id,
                concept_name=concept.lower().strip(),
                rating=payload.rating,
                target_depth=payload.target_depth
            )
            return res
    except Exception:
        initial_params = {"stability": 0.8, "difficulty": 0.3, "mastery": 0.5}
        result = mastery_engine.review(initial_params, payload.rating)
        return {**result, "concept": concept, "status": "simulated_local"}
