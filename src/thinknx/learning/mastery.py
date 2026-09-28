import json
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


def compute_retrievability(stability: float, elapsed_days: float) -> float:
    """FSRS power-law forgetting curve: R = (1 + 0.235·t/S)^-0.5"""
    if stability <= 0 or elapsed_days <= 0:
        return 1.0
    return (1.0 + 0.235 * elapsed_days / stability) ** -0.5


class FSRSMastery:
    """
    Spaced repetition engine wrapping FSRS.
    Persists the full Card state as JSON on the KNOWS edge so that due dates,
    stability, and state survive between reviews.
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
        """Return default parameters for a brand-new concept."""
        return {
            "stability": 0.4,
            "difficulty": 0.3,
            "retrievability": 1.0,
            "mastery": 0.0,
            "depth": "surface",
            "card_json": None,
        }

    def _card_from_params(self, params: Dict[str, Any]) -> Any:
        """Restore a Card from persisted card_json, or build from legacy fields."""
        if Card is None:
            return None
        card_json = params.get("card_json")
        if card_json:
            try:
                data = json.loads(card_json) if isinstance(card_json, str) else card_json
                if hasattr(Card, "from_dict"):
                    return Card.from_dict(data)
            except Exception:
                pass
        card = Card()
        if params.get("stability") is not None:
            card.stability = float(params["stability"])
        if params.get("difficulty") is not None:
            card.difficulty = float(params["difficulty"])
        return card

    def _card_to_json(self, card: Any) -> str:
        if hasattr(card, "to_dict"):
            return json.dumps(card.to_dict(), default=str)
        return json.dumps({
            "stability": getattr(card, "stability", 0.4),
            "difficulty": getattr(card, "difficulty", 0.3),
            "due": getattr(card, "due", datetime.now(timezone.utc)).isoformat()
                if hasattr(getattr(card, "due", None), "isoformat") else None,
        })

    def review(self, current_params: Dict[str, Any], rating: int) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        rating = max(1, min(4, rating))

        if self.scheduler is not None and Card is not None and Rating is not None:
            try:
                card = self._card_from_params(current_params)
                rating_map = {1: Rating.Again, 2: Rating.Hard, 3: Rating.Good, 4: Rating.Easy}
                rating_obj = rating_map.get(rating, Rating.Good)

                res = self.scheduler.review_card(card, rating_obj, now)
                new_card = res[0] if isinstance(res, (tuple, list)) else res

                stability = float(getattr(new_card, "stability", 1.0))
                difficulty = float(getattr(new_card, "difficulty", 0.3))
                mastery = self._compute_mastery(stability, difficulty, rating)

                due_dt = getattr(new_card, "due", None)
                due_iso = due_dt.isoformat() if hasattr(due_dt, "isoformat") else None

                return {
                    "mastery": mastery,
                    "stability": round(stability, 4),
                    "difficulty": round(difficulty, 4),
                    "retrievability": 1.0,
                    "due": due_iso,
                    "card_json": self._card_to_json(new_card),
                }
            except Exception as e:
                logger.warning("FSRS scheduler error, using analytic model", error=str(e))

        prev_s = float(current_params.get("stability", 0.4) or 0.4)
        prev_d = float(current_params.get("difficulty", 0.3) or 0.3)

        if rating == 1:
            new_s = max(0.2, prev_s * 0.4)
            new_d = min(1.0, prev_d + 0.15)
        elif rating == 2:
            new_s = prev_s * 1.2
            new_d = min(1.0, prev_d + 0.05)
        elif rating == 3:
            new_s = prev_s * 2.5
            new_d = max(0.0, prev_d - 0.05)
        else:
            new_s = prev_s * 4.0
            new_d = max(0.0, prev_d - 0.15)

        interval_days = max(1.0, new_s * 0.9)
        from datetime import timedelta
        due = (now + timedelta(days=interval_days)).isoformat()

        mastery = self._compute_mastery(new_s, new_d, rating)
        return {
            "mastery": mastery,
            "stability": round(new_s, 4),
            "difficulty": round(new_d, 4),
            "retrievability": 1.0,
            "due": due,
            "card_json": None,
        }

    def _compute_mastery(self, stability: float, difficulty: float, latest_rating: int) -> float:
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
        user_concepts = await queries.get_user_concepts(session, user_id)
        current = next((c for c in user_concepts if c["concept"] == concept_name), None)

        if not current:
            await queries.add_user_concept(session, user_id, concept_name)
            current = {"stability": 0.4, "difficulty": 0.3, "mastery": 0.1, "depth": "surface"}

        updated = self.review(current, rating)

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
            depth=new_depth,
            due=updated.get("due"),
            card_json=updated.get("card_json"),
        )

        if rating == 1:
            logger.info("Propagating failure", concept=concept_name, user_id=user_id)
            await queries.propagate_failure(session, user_id, concept_name, decay_factor=0.75)

        return {**updated, "concept": concept_name, "depth": new_depth}
