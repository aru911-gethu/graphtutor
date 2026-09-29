import uuid
from typing import List, Dict, Any, Optional
from thinknx.assessment.models import SkillTag, StateTag


class SkillReportGenerator:
    """Generates multidimensional skill mastery reports and shareable challenge payloads."""

    DOMAIN_MAPPING: Dict[str, str] = {
        "transformers": "Deep Learning",
        "attention-mechanism": "Deep Learning",
        "neural-networks": "Machine Learning",
        "gradient-descent": "Machine Learning",
        "backpropagation": "Deep Learning",
        "linear-algebra": "Mathematics",
        "calculus": "Mathematics",
        "docker": "Infrastructure",
        "kubernetes": "Infrastructure",
        "rag": "AI Engineering",
        "vector-databases": "AI Engineering",
        "python": "Programming",
        "git": "Tools & Workflow",
    }

    @classmethod
    def get_domain(cls, concept_slug: str) -> str:
        slug = concept_slug.lower().strip()
        return cls.DOMAIN_MAPPING.get(slug, "General CS")

    @classmethod
    def generate_report(
        cls,
        user_id: str,
        user_concepts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        domain_scores: Dict[str, List[float]] = {}
        skill_counts: Dict[str, int] = {tag.value: 0 for tag in SkillTag}
        fragile_concepts: List[str] = []
        blocker_concepts: List[str] = []

        total_theta = 0.0
        active_count = 0

        for item in user_concepts:
            slug = item.get("concept", item.get("name", "unknown"))
            theta = float(item.get("theta", item.get("mastery", 0.5)))
            skill_tag_val = item.get("skill_tag", SkillTag.EXPOSED.value)
            state_tags = item.get("state_tags", [])

            if skill_tag_val in skill_counts:
                skill_counts[skill_tag_val] += 1
            else:
                skill_counts[SkillTag.EXPOSED.value] += 1

            if StateTag.FRAGILE.value in state_tags or StateTag.FRAGILE in state_tags:
                fragile_concepts.append(slug)
            if StateTag.BLOCKER.value in state_tags or StateTag.BLOCKER in state_tags:
                blocker_concepts.append(slug)

            domain = cls.get_domain(slug)
            if domain not in domain_scores:
                domain_scores[domain] = []
            domain_scores[domain].append(theta)

            total_theta += theta
            active_count += 1

        radar_axes = []
        for domain, scores in domain_scores.items():
            avg_score = sum(scores) / len(scores) if scores else 0.0
            radar_axes.append({
                "domain": domain,
                "score": round(avg_score * 100, 1),
                "concept_count": len(scores)
            })

        overall_ability = round((total_theta / active_count) * 100, 1) if active_count > 0 else 50.0

        return {
            "user_id": user_id,
            "overall_ability": overall_ability,
            "total_assessed_concepts": active_count,
            "skill_breakdown": skill_counts,
            "radar_chart": radar_axes,
            "friction_alerts": {
                "fragile": fragile_concepts,
                "blockers": blocker_concepts
            }
        }

    @staticmethod
    def create_challenge_payload(
        creator_id: str,
        concept_slug: str,
        creator_score: float,
        question_ids: List[str],
        base_url: str = "http://localhost:3000"
    ) -> Dict[str, Any]:
        challenge_id = f"chl_{uuid.uuid4().hex[:12]}"
        share_url = f"{base_url.rstrip('/')}/challenge/{challenge_id}"
        return {
            "challenge_id": challenge_id,
            "share_url": share_url,
            "creator_id": creator_id,
            "concept_slug": concept_slug,
            "creator_score": round(creator_score, 2),
            "question_ids": question_ids,
            "summary": f"Can you beat my score of {int(creator_score * 100)}% on {concept_slug}?"
        }
