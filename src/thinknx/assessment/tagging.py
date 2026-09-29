from typing import List
from thinknx.assessment.models import SkillTag, StateTag


class SkillTagger:
    """Evaluates evidence-based skill mastery tags and cognitive state flags."""

    @staticmethod
    def derive_skill_tag(
        theta: float,
        retrievability: float = 1.0,
        review_count: int = 0
    ) -> SkillTag:
        if review_count == 0:
            return SkillTag.UNSEEN

        if theta >= 0.9 and retrievability >= 0.85:
            return SkillTag.MASTERED
        elif theta >= 0.8:
            return SkillTag.EXPLAINS
        elif theta >= 0.6:
            return SkillTag.APPLIES
        elif theta >= 0.3:
            return SkillTag.RECOGNIZES
        else:
            return SkillTag.EXPOSED

    @staticmethod
    def derive_state_tags(
        theta: float,
        retrievability: float,
        stability: float,
        review_count: int,
        consecutive_fails: int = 0,
        response_time_ms: int = 5000,
        last_is_correct: bool = True,
        dependent_count: int = 0
    ) -> List[StateTag]:
        tags = []

        if theta < 0.5 and dependent_count >= 2:
            tags.append(StateTag.BLOCKER)

        if retrievability < 0.6 and review_count >= 1:
            tags.append(StateTag.RUSTY)

        if theta >= 0.6 and stability < 7.0 and review_count <= 3:
            tags.append(StateTag.FRAGILE)

        if consecutive_fails >= 2:
            tags.append(StateTag.MISCONCEPTION)

        if not last_is_correct and response_time_ms < 3000:
            tags.append(StateTag.OVERCONFIDENT)

        if response_time_ms < 2000 and review_count >= 2:
            tags.append(StateTag.GUESSING)

        return tags if tags else [StateTag.NONE]
