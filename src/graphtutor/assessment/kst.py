from typing import List, Dict, Optional, Any


class KSTPropagator:
    """Knowledge Space Theory DAG evidence propagation."""

    def __init__(self, positive_reinforcement: float = 0.05):
        self.positive_reinforcement = positive_reinforcement

    def propagate_success(
        self,
        prerequisites: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Weak positive evidence flows to prerequisites on success."""
        updates = {}
        for p in prerequisites:
            slug = p.get("concept") or p.get("name")
            current_theta = float(p.get("theta", p.get("mastery", 0.5)))
            boosted = current_theta + self.positive_reinforcement * (1.0 - current_theta)
            updates[slug] = round(boosted, 4)
        return updates

    def identify_diagnostic_probe(
        self,
        prerequisites: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Identify weakest prerequisite to probe on failure."""
        if not prerequisites:
            return None
        sorted_prereqs = sorted(
            prerequisites,
            key=lambda p: float(p.get("theta", p.get("mastery", 0.5)))
        )
        weakest = sorted_prereqs[0]
        return weakest.get("concept") or weakest.get("name")
