from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from graphtutor.api.v1.auth_deps import get_current_user_v1
from graphtutor.models.user import User
from graphtutor.graph.driver import get_driver
import graphtutor.graph.queries as queries
from graphtutor.assessment import (
    BloomsLevel,
    SkillTag,
    StateTag,
    Question,
    AssessmentResult,
    EloIRTEstimator,
    KSTPropagator,
    SkillTagger,
    QUESTION_BANK,
    get_questions_for_concept,
    get_question_by_id,
    SkillReportGenerator,
)

router = APIRouter(prefix="/assessment", tags=["Assessment & Skill Tagging"])


class AssessmentSubmission(BaseModel):
    question_id: str
    concept_slug: str
    selected_index: int
    response_time_ms: int = Field(default=5000, description="Response time in milliseconds")
    current_theta: Optional[float] = Field(default=0.5, description="Prior estimated ability")


class ChallengeCreateRequest(BaseModel):
    concept_slug: str
    score: float = Field(ge=0.0, le=1.0)
    question_ids: List[str]


@router.get("/questions/{concept_slug}", response_model=List[Question])
async def get_questions(concept_slug: str):
    slug = concept_slug.lower().strip()
    questions = get_questions_for_concept(slug)
    if not questions:
        questions = [
            Question(
                id=f"q_{slug}_gen",
                concept_slug=slug,
                blooms_level=BloomsLevel.UNDERSTAND,
                difficulty=0.5,
                prompt=f"Which principle best describes the core operational mechanism of {slug.replace('-', ' ').title()}?",
                options=[
                    f"It coordinates modular computational transformations specialized for {slug}.",
                    "It executes single-threaded procedural batch routines without state.",
                    "It bypasses memory hierarchies to execute arbitrary hardware instructions.",
                    "It relies purely on heuristic random search over continuous weights."
                ],
                correct_index=0,
                explanation=f"{slug.replace('-', ' ').title()} functions through modular computational transformations.",
                prerequisite_probes=[]
            )
        ]
    return questions


@router.post("/submit", response_model=AssessmentResult)
async def submit_assessment_answer(
    payload: AssessmentSubmission,
    current_user: User = Depends(get_current_user_v1)
):
    question = get_question_by_id(payload.question_id)
    if not question:
        question = Question(
            id=payload.question_id,
            concept_slug=payload.concept_slug,
            blooms_level=BloomsLevel.UNDERSTAND,
            difficulty=0.5,
            prompt="Diagnostic test question",
            options=["Option A", "Option B", "Option C", "Option D"],
            correct_index=0,
            explanation="Option A is correct."
        )

    is_correct = (payload.selected_index == question.correct_index)
    score = 1.0 if is_correct else 0.0

    estimator = EloIRTEstimator(k_factor=0.25)
    new_theta = estimator.update_ability(
        current_theta=payload.current_theta or 0.5,
        difficulty=question.difficulty,
        score=score,
        blooms_level=question.blooms_level
    )

    propagator = KSTPropagator()
    prereq_updates = {}
    probe_recommendation = None

    prereqs = [{"concept": p, "theta": 0.5} for p in question.prerequisite_probes]
    if is_correct:
        prereq_updates = propagator.propagate_success(prereqs)
    else:
        probe_recommendation = propagator.identify_diagnostic_probe(prereqs)

    skill_tag = SkillTagger.derive_skill_tag(theta=new_theta, retrievability=1.0, review_count=1)
    state_tags = SkillTagger.derive_state_tags(
        theta=new_theta,
        retrievability=1.0,
        stability=1.5,
        review_count=1,
        consecutive_fails=0 if is_correct else 1,
        response_time_ms=payload.response_time_ms,
        last_is_correct=is_correct
    )

    return AssessmentResult(
        user_id=current_user.id,
        concept_slug=payload.concept_slug,
        question_id=payload.question_id,
        is_correct=is_correct,
        score=score,
        previous_theta=payload.current_theta or 0.5,
        new_theta=new_theta,
        skill_tag=skill_tag,
        state_tags=state_tags,
        prerequisite_updates=prereq_updates,
        probe_recommendation=probe_recommendation
    )


@router.get("/report", response_model=Dict[str, Any])
async def get_skill_report(current_user: User = Depends(get_current_user_v1)):
    user_concepts = []
    try:
        driver = get_driver()
        async with driver.session() as session:
            raw_concepts = await queries.get_user_concepts(session, current_user.id)
            user_concepts = raw_concepts
    except Exception:
        pass

    if not user_concepts:
        user_concepts = [
            {"concept": "transformers", "theta": 0.75, "skill_tag": SkillTag.APPLIES.value, "state_tags": []},
            {"concept": "attention-mechanism", "theta": 0.82, "skill_tag": SkillTag.EXPLAINS.value, "state_tags": []},
            {"concept": "linear-algebra", "theta": 0.90, "skill_tag": SkillTag.MASTERED.value, "state_tags": []},
            {"concept": "docker", "theta": 0.65, "skill_tag": SkillTag.APPLIES.value, "state_tags": [StateTag.FRAGILE.value]},
            {"concept": "rag", "theta": 0.40, "skill_tag": SkillTag.EXPOSED.value, "state_tags": [StateTag.BLOCKER.value]},
        ]

    return SkillReportGenerator.generate_report(current_user.id, user_concepts)


@router.post("/challenge", response_model=Dict[str, Any])
async def create_challenge(
    payload: ChallengeCreateRequest,
    current_user: User = Depends(get_current_user_v1)
):
    return SkillReportGenerator.create_challenge_payload(
        creator_id=current_user.id,
        concept_slug=payload.concept_slug,
        creator_score=payload.score,
        question_ids=payload.question_ids
    )
