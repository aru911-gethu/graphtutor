from datetime import datetime, timezone
from typing import Dict, Any, Optional
import structlog
from neo4j import AsyncSession

import thinknx.graph.queries as queries

logger = structlog.get_logger(__name__)

try:
    from fsrs import Scheduler, Card, Rating
except ImportError:
    try:
        from fsrs import FSRS as Scheduler, Card, Rating
    except ImportError:
        Scheduler = None
        Card = None
        Rating = None


class FSRSMastery:
    """
    Spaced repetition engine wrapping FSRS (Free Spaced Repetition Scheduler).
    Tracks memory stability (S), item difficulty (D), and retrievability (R).
    Handles failure propagation across dependent concepts in the knowledge graph.
    """

    def __init__(self, desired_retention: float = 0.9):
        self.desired_retention = desired_retention
        if Scheduler is not None:
            try:
                self.scheduler = Scheduler(desired_retention=desired_retention)
            except Exception:
                self.scheduler = Scheduler()
        else:
            self.scheduler = None

    def new_card(self) -> Dict[str, Any]:
        """Generate initial FSRS parameters for a newly acquired concept."""
        if Card is not None:
            card = Card()
            stability = getattr(card, "stability", 0.4) or 0.4
            difficulty = getattr(card, "difficulty", 0.3) or 0.3
        else:
            stability = 0.4
            difficulty = 0.3

        return {
            "mastery": 0.1,
            "stability": round(float(stability), 4),
            "difficulty": round(float(difficulty), 4),
            "retrievability": 1.0,
            "depth": "surface",
            "last_review": datetime.now(timezone.utc).isoformat(),
        }

    def review(self, current_params: Dict[str, Any], rating: int) -> Dict[str, Any]:
        """
        Process a review attempt.
        rating: 1=Again (failed), 2=Hard, 3=Good, 4=Easy
        Returns updated FSRS parameters, retrievability, and computed mastery.
        """
        now = datetime.now(timezone.utc)
        rating = max(1, min(4, rating))

        if self.scheduler is not None and Card is not None and Rating is not None:
            try:
                card = Card()
                if current_params.get("stability") is not None:
                    card.stability = float(current_params["stability"])
                if current_params.get("difficulty") is not None:
                    card.difficulty = float(current_params["difficulty"])

                rating_map = {
                    1: Rating.Again,
                    2: Rating.Hard,
                    3: Rating.Good,
                    4: Rating.Easy,
                }
                rating_obj = rating_map.get(rating, Rating.Good)

                # Execute review step
                res = self.scheduler.review_card(card, rating_obj, now)
                new_card = res[0] if isinstance(res, (tuple, list)) else res

                # Determine retrievability
                retrievability = 1.0
                if hasattr(self.scheduler, "get_card_retrievability"):
                    retrievability = self.scheduler.get_card_retrievability(new_card, now)
                elif hasattr(new_card, "retrievability"):
                    r_val = getattr(new_card, "retrievability")
                    retrievability = r_val(now) if callable(r_val) else r_val

                stability = float(getattr(new_card, "stability", 1.0))
                difficulty = float(getattr(new_card, "difficulty", 0.3))
                mastery = self._compute_mastery(stability, difficulty, rating)

                due_dt = getattr(new_card, "due", None)
                next_review = due_dt.isoformat() if hasattr(due_dt, "isoformat") else None

                return {
                    "mastery": mastery,
                    "stability": round(stability, 4),
                    "difficulty": round(difficulty, 4),
                    "retrievability": round(float(retrievability), 4),
                    "next_review": next_review,
                }
            except Exception as e:
                logger.warning("FSRS scheduler calculation error, using analytic model", error=str(e))

        # Analytic fallback formula
        prev_s = float(current_params.get("stability", 0.4) or 0.4)
        prev_d = float(current_params.get("difficulty", 0.3) or 0.3)

        if rating == 1:  # Again
            new_s = max(0.2, prev_s * 0.4)
            new_d = min(1.0, prev_d + 0.15)
        elif rating == 2:  # Hard
            new_s = prev_s * 1.2
            new_d = min(1.0, prev_d + 0.05)
        elif rating == 3:  # Good
            new_s = prev_s * 2.5
            new_d = max(0.0, prev_d - 0.05)
        else:  # Easy
            new_s = prev_s * 4.0
            new_d = max(0.0, prev_d - 0.15)

        mastery = self._compute_mastery(new_s, new_d, rating)
        return {
            "mastery": mastery,
            "stability": round(new_s, 4),
            "difficulty": round(new_d, 4),
            "retrievability": 1.0,
            "next_review": None,
        }

    def _compute_mastery(self, stability: float, difficulty: float, latest_rating: int) -> float:
        """
        Derive mastery score (0.0 - 1.0) from stability, difficulty, and quiz score.
        Formula: 40% stability (capped at 180 days) + 30% inverted difficulty + 30% rating.
        """
        stability_score = min(stability / 180.0, 1.0)
        difficulty_score = max(0.0, min(1.0, 1.0 - (difficulty / 10.0 if difficulty > 1.0 else difficulty)))
        rating_score = (latest_rating - 1) / 3.0
        mastery = 0.4 * stability_score + 0.3 * difficulty_score + 0.3 * rating_score
        return round(max(0.0, min(1.0, mastery)), 3)

    async def record_review(
        self,
        session: AsyncSession,
        user_id: str,
        concept_name: str,
        rating: int,
        target_depth: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process review, update Neo4j node, and propagate failure to dependents if failed.
        """
        user_concepts = await queries.get_user_concepts(session, user_id)
        current = next((c for c in user_concepts if c["concept"] == concept_name), None)

        if not current:
            # Concept wasn't added yet, add it first
            await queries.add_user_concept(session, user_id, concept_name)
            current = {"stability": 0.4, "difficulty": 0.3, "mastery": 0.1, "depth": "surface"}

        updated = self.review(current, rating)

        # Upgrade depth if mastery increases past thresholds
        new_depth = current.get("depth", "surface")
        if target_depth:
            new_depth = target_depth
        elif updated["mastery"] >= 0.85:
            new_depth = "deep"
        elif updated["mastery"] >= 0.5:
            new_depth = "working"

        await queries.update_mastery(
            session=session,
            user_id=user_id,
            concept_name=concept_name,
            mastery=updated["mastery"],
            stability=updated["stability"],
            difficulty=updated["difficulty"],
            retrievability=updated["retrievability"],
            rating=rating,
            depth=new_depth
        )

        # Graph-aware failure propagation
        if rating == 1:
            logger.info("Propagating concept failure to downstream dependents", concept=concept_name, user_id=user_id)
            await queries.propagate_failure(session, user_id, concept_name, decay_factor=0.75)

        return {**updated, "concept": concept_name, "depth": new_depth}
