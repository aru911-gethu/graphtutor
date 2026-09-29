import pytest
from thinknx.assessment import (
    BloomsLevel,
    SkillTag,
    StateTag,
    EloIRTEstimator,
    KSTPropagator,
    SkillTagger,
    SkillReportGenerator,
)


def test_elo_irt_ability_update():
    estimator = EloIRTEstimator(k_factor=0.25)

    theta_before = 0.50
    diff = 0.50
    theta_after = estimator.update_ability(
        current_theta=theta_before,
        difficulty=diff,
        score=1.0,
        blooms_level=BloomsLevel.UNDERSTAND
    )
    assert theta_after > theta_before

    delta_understand = theta_after - theta_before
    theta_after_eval = estimator.update_ability(
        current_theta=theta_before,
        difficulty=diff,
        score=1.0,
        blooms_level=BloomsLevel.EVALUATE
    )
    delta_eval = theta_after_eval - theta_before
    assert delta_eval > delta_understand

    theta_fail = estimator.update_ability(
        current_theta=theta_before,
        difficulty=diff,
        score=0.0,
        blooms_level=BloomsLevel.UNDERSTAND
    )
    assert theta_fail < theta_before


def test_kst_propagation():
    propagator = KSTPropagator(positive_reinforcement=0.1)

    prereqs = [
        {"concept": "linear-algebra", "theta": 0.5},
        {"concept": "attention-mechanism", "theta": 0.3},
    ]

    updates = propagator.propagate_success(prereqs)
    assert updates["linear-algebra"] > 0.5
    assert updates["attention-mechanism"] > 0.3

    probe = propagator.identify_diagnostic_probe(prereqs)
    assert probe == "attention-mechanism"


def test_skill_and_state_tagging():
    assert SkillTagger.derive_skill_tag(theta=0.5, review_count=0) == SkillTag.UNSEEN
    assert SkillTagger.derive_skill_tag(theta=0.92, retrievability=0.90, review_count=5) == SkillTag.MASTERED
    assert SkillTagger.derive_skill_tag(theta=0.82, review_count=2) == SkillTag.EXPLAINS

    blocker_tags = SkillTagger.derive_state_tags(
        theta=0.3,
        retrievability=0.9,
        stability=10.0,
        review_count=1,
        dependent_count=3
    )
    assert StateTag.BLOCKER in blocker_tags

    rusty_tags = SkillTagger.derive_state_tags(
        theta=0.8,
        retrievability=0.45,
        stability=10.0,
        review_count=3
    )
    assert StateTag.RUSTY in rusty_tags

    overconf_tags = SkillTagger.derive_state_tags(
        theta=0.6,
        retrievability=0.9,
        stability=10.0,
        review_count=2,
        response_time_ms=1500,
        last_is_correct=False
    )
    assert StateTag.OVERCONFIDENT in overconf_tags


def test_skill_report_generation():
    concepts = [
        {"concept": "transformers", "theta": 0.8, "skill_tag": SkillTag.EXPLAINS.value, "state_tags": []},
        {"concept": "attention-mechanism", "theta": 0.7, "skill_tag": SkillTag.APPLIES.value, "state_tags": []},
        {"concept": "linear-algebra", "theta": 0.9, "skill_tag": SkillTag.MASTERED.value, "state_tags": []},
        {"concept": "docker", "theta": 0.5, "skill_tag": SkillTag.RECOGNIZES.value, "state_tags": [StateTag.FRAGILE.value]},
    ]

    report = SkillReportGenerator.generate_report("test_user", concepts)
    assert report["user_id"] == "test_user"
    assert report["total_assessed_concepts"] == 4
    assert len(report["radar_chart"]) >= 2
    assert "Deep Learning" in [axis["domain"] for axis in report["radar_chart"]]
    assert "Mathematics" in [axis["domain"] for axis in report["radar_chart"]]
    assert "docker" in report["friction_alerts"]["fragile"]


def test_challenge_creation():
    chl = SkillReportGenerator.create_challenge_payload(
        creator_id="user_123",
        concept_slug="transformers",
        creator_score=0.95,
        question_ids=["q_trans_1", "q_trans_2"]
    )
    assert chl["creator_id"] == "user_123"
    assert "/challenge/chl_" in chl["share_url"]
    assert "95%" in chl["summary"]
