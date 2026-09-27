from typing import List, Dict, Any, Optional
from neo4j import AsyncSession
import structlog

import thinknx.graph.queries as queries

logger = structlog.get_logger(__name__)


class PathGenerator:
    """Computes dependency-ordered learning paths towards user goals."""

    async def get_path_for_goal(
        self,
        session: AsyncSession,
        user_id: str,
        goal_concept: str
    ) -> Dict[str, Any]:
        """
        Calculates an ordered learning roadmap from unmastered prerequisites to goal.
        Returns total steps, completed prerequisites, and the next recommended step.
        """
        # Fetch path prerequisites from Neo4j
        raw_path = await queries.get_learning_path(session, user_id, goal_concept)
        user_concepts = await queries.get_user_concepts(session, user_id)
        user_map = {c["concept"]: c for c in user_concepts}

        steps = []
        for item in raw_path:
            c_name = item.get("concept")
            display_name = item.get("displayName") or c_name
            known = user_map.get(c_name, {})
            mastery = known.get("mastery", 0.0)
            depth = known.get("depth", "surface")

            steps.append({
                "concept": c_name,
                "displayName": display_name,
                "complexity": item.get("complexity", 0.5),
                "depth": depth,
                "mastery": mastery,
                "status": "mastered" if mastery >= 0.75 else ("in_progress" if mastery > 0.2 else "locked"),
            })

        # Next actionable step is the first one not mastered
        next_step = next((s for s in steps if s["status"] != "mastered"), None)

        return {
            "goal": goal_concept,
            "total_steps": len(steps),
            "steps": steps,
            "next_step": next_step,
            "is_completed": len(steps) > 0 and all(s["status"] == "mastered" for s in steps),
        }
