from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException

from graphtutor.api.v1.auth_deps import get_current_user_v1
from graphtutor.models.user import User
from graphtutor.graph.driver import get_driver
from graphtutor.learning.paths import PathGenerator

router = APIRouter(prefix="/path", tags=["Learning Paths"])

FALLBACK_PATHS = {
    "transformers": {
        "goal": "transformers",
        "total_steps": 4,
        "steps": [
            {"concept": "linear-algebra", "displayName": "Linear Algebra", "complexity": 0.4, "mastery": 0.85, "status": "mastered"},
            {"concept": "machine-learning", "displayName": "Machine Learning", "complexity": 0.5, "mastery": 0.70, "status": "mastered"},
            {"concept": "attention-mechanism", "displayName": "Attention Mechanism", "complexity": 0.7, "mastery": 0.40, "status": "in_progress"},
            {"concept": "transformers", "displayName": "Transformers", "complexity": 0.7, "mastery": 0.20, "status": "locked"},
        ],
        "next_step": {"concept": "attention-mechanism", "displayName": "Attention Mechanism", "complexity": 0.7, "mastery": 0.40, "status": "in_progress"},
        "is_completed": False
    }
}


@router.get("", response_model=Dict[str, Any])
async def get_path(
    goal: str = Query(..., description="Target concept or learning goal slug"),
    current_user: User = Depends(get_current_user_v1)
):
    goal_slug = goal.lower().strip()
    generator = PathGenerator()

    try:
        driver = get_driver()
        async with driver.session() as session:
            path_data = await generator.get_path_for_goal(session, current_user.id, goal_slug)
            if path_data.get("steps"):
                return path_data
    except Exception:
        pass

    if goal_slug in FALLBACK_PATHS:
        return FALLBACK_PATHS[goal_slug]

    return {
        "goal": goal_slug,
        "total_steps": 2,
        "steps": [
            {"concept": "python", "displayName": "Python", "complexity": 0.3, "mastery": 0.8, "status": "mastered"},
            {"concept": goal_slug, "displayName": goal_slug.replace("-", " ").title(), "complexity": 0.6, "mastery": 0.1, "status": "in_progress"}
        ],
        "next_step": {"concept": goal_slug, "displayName": goal_slug.replace("-", " ").title(), "complexity": 0.6, "mastery": 0.1, "status": "in_progress"},
        "is_completed": False
    }
