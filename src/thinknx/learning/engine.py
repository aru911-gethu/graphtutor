import re
from typing import Dict, Any, Optional, List
import structlog
from neo4j import AsyncDriver

import thinknx.graph.queries as queries
from thinknx.graph.driver import get_driver
from thinknx.learning.mastery import FSRSMastery
from thinknx.learning.explainer import AdaptiveExplainer
from thinknx.learning.quiz import QuizGenerator
from thinknx.learning.paths import PathGenerator
from thinknx.store.cache import LLMCache
from thinknx.config import settings

logger = structlog.get_logger(__name__)


def slugify(text: str) -> str:
    """Convert text to lowercase hyphenated concept slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "-", text).strip("-")


class LearningEngine:
    """
    Central learning loop orchestrator:
    1. Assesses student's current knowledge in Neo4j
    2. Generates polymorphic visual lesson (6 themes)
    3. Generates verification quiz
    4. Evaluates responses and updates FSRS spaced repetition
    5. Propagates failures along prerequisite edges
    """

    def __init__(
        self,
        driver: Optional[AsyncDriver] = None,
        mastery: Optional[FSRSMastery] = None,
        explainer: Optional[AdaptiveExplainer] = None,
        quiz: Optional[QuizGenerator] = None,
        paths: Optional[PathGenerator] = None,
        cache: Optional[LLMCache] = None,
    ):
        self.driver = driver or get_driver()
        self.mastery = mastery or FSRSMastery()
        self.explainer = explainer or AdaptiveExplainer()
        self.quiz = quiz or QuizGenerator()
        self.paths = paths or PathGenerator()
        self.cache = cache or LLMCache()

    async def teach(
        self,
        user_id: str,
        topic: str,
        target_depth: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes full teaching cycle:
        - Resolves concept node in Neo4j
        - Inspects current mastery and known concepts
        - Synthesizes polymorphic lesson payload (code remarks, visual architecture, math symbols)
        - Prepares quiz questions
        """
        concept_slug = slugify(topic)
        display_name = topic.strip().title()

        async with self.driver.session() as session:
            # 1. Find or create concept node
            concept = await queries.create_or_get_concept(
                session=session,
                name=concept_slug,
                display_name=display_name,
                domain="ai-ml",
                complexity=0.5
            )

            # 2. Get user's active knowledge state
            user_concepts = await queries.get_user_concepts(session, user_id)
            known_concepts = [c["displayName"] for c in user_concepts if c["mastery"] >= 0.5]
            existing = next((c for c in user_concepts if c["concept"] == concept_slug), None)

            current_depth = target_depth or (existing["depth"] if existing else "surface")

            # 3. Add to user's graph if first time
            if not existing:
                await queries.add_user_concept(
                    session=session,
                    user_id=user_id,
                    concept_name=concept_slug,
                    mastery=0.1,
                    depth=current_depth
                )

        # 4. Generate adaptive lesson payload (supports all 6 themes)
        lesson_payload = await self.explainer.explain(
            concept=display_name,
            level=current_depth,
            known_concepts=known_concepts[:6],
            previous_analogies=existing.get("explanationsThatWorked", []) if existing else []
        )

        # 5. Generate quiz questions
        quiz_data = await self.quiz.generate(
            concept=display_name,
            level=current_depth,
            count=2,
            mastery_context=f"Mastery: {existing['mastery']:.0%}" if existing else "First encounter"
        )

        return {
            "concept": concept,
            "lesson": lesson_payload,
            "explanation": lesson_payload.content,
            "quiz": quiz_data,
            "current_depth": current_depth,
        }

    async def evaluate_answer(
        self,
        user_id: str,
        concept_name: str,
        question: str,
        correct_answer: str,
        student_answer: str,
        target_depth: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates user's answer, computes FSRS rating, and updates Neo4j.
        """
        concept_slug = slugify(concept_name)

        # 1. Evaluate with LLM or heuristic
        eval_result = await self.quiz.evaluate_answer(
            question=question,
            correct_answer=correct_answer,
            student_answer=student_answer
        )

        rating = eval_result.get("fsrs_rating", 3 if eval_result.get("correct") else 1)

        # 2. Record review in FSRS and Neo4j
        async with self.driver.session() as session:
            review_result = await self.mastery.record_review(
                session=session,
                user_id=user_id,
                concept_name=concept_slug,
                rating=rating,
                target_depth=target_depth
            )

        return {
            "correct": eval_result["correct"],
            "score": eval_result["score"],
            "feedback": eval_result["feedback"],
            "rating": rating,
            "mastery": review_result["mastery"],
            "depth": review_result["depth"],
            "retrievability": review_result["retrievability"],
        }

    async def get_progress(self, user_id: str) -> Dict[str, Any]:
        """Fetch dashboard progress and mastery statistics."""
        async with self.driver.session() as session:
            return await queries.get_user_stats(session, user_id)

    async def get_next_topics(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch recommended next concepts whose prerequisites are satisfied."""
        async with self.driver.session() as session:
            return await queries.get_next_topics(session, user_id, limit=limit)

    async def get_learning_path(self, user_id: str, goal_concept: str) -> Dict[str, Any]:
        """Fetch dependency-ordered roadmap to a goal concept."""
        concept_slug = slugify(goal_concept)
        async with self.driver.session() as session:
            return await self.paths.get_path_for_goal(session, user_id, concept_slug)
