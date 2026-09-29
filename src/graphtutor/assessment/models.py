from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class BloomsLevel(str, Enum):
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class SkillTag(str, Enum):
    UNSEEN = "unseen"
    EXPOSED = "exposed"
    RECOGNIZES = "recognizes"
    APPLIES = "applies"
    EXPLAINS = "explains"
    MASTERED = "mastered"


class StateTag(str, Enum):
    NONE = "healthy"
    FRAGILE = "fragile"
    RUSTY = "rusty"
    MISCONCEPTION = "misconception"
    OVERCONFIDENT = "overconfident"
    GUESSING = "guessing"
    BLOCKER = "blocker"


class Question(BaseModel):
    id: str
    concept_slug: str
    blooms_level: BloomsLevel
    difficulty: float = Field(default=0.5, ge=0.0, le=1.0)
    prompt: str
    options: List[str]
    correct_index: int
    explanation: str
    prerequisite_probes: List[str] = Field(default_factory=list)


class AssessmentResult(BaseModel):
    user_id: str
    concept_slug: str
    question_id: str
    is_correct: bool
    score: float
    previous_theta: float
    new_theta: float
    skill_tag: SkillTag
    state_tags: List[StateTag] = Field(default_factory=list)
    prerequisite_updates: Dict[str, float] = Field(default_factory=dict)
    probe_recommendation: Optional[str] = None
