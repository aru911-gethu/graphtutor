import math
from typing import Dict
from thinknx.assessment.models import BloomsLevel

BLOOMS_WEIGHTS: Dict[BloomsLevel, float] = {
    BloomsLevel.REMEMBER: 0.8,
    BloomsLevel.UNDERSTAND: 1.0,
    BloomsLevel.APPLY: 1.2,
    BloomsLevel.ANALYZE: 1.4,
    BloomsLevel.EVALUATE: 1.6,
    BloomsLevel.CREATE: 1.8,
}


class EloIRTEstimator:
    """
    Elo-Item Response Theory (Pelánek 2016) ability estimator.
    Separates latent cognitive ability (theta) from memory decay/retention (FSRS).
    """

    def __init__(self, k_factor: float = 0.25):
        self.k_factor = k_factor

    def predict_probability(self, theta: float, difficulty: float) -> float:
        """Rasch logistic model: P(correct | theta, difficulty)."""
        scaled_theta = (theta - 0.5) * 6.0
        scaled_diff = (difficulty - 0.5) * 6.0
        logit = scaled_theta - scaled_diff
        clamped_logit = max(-10.0, min(10.0, logit))
        return 1.0 / (1.0 + math.exp(-clamped_logit))

    def update_ability(
        self,
        current_theta: float,
        difficulty: float,
        score: float,
        blooms_level: BloomsLevel = BloomsLevel.UNDERSTAND
    ) -> float:
        """Update theta using Elo-IRT gradient step: theta + K * weight * (score - P)."""
        p_correct = self.predict_probability(current_theta, difficulty)
        weight = BLOOMS_WEIGHTS.get(blooms_level, 1.0)
        delta = self.k_factor * weight * (score - p_correct)
        new_theta = current_theta + delta
        return round(max(0.01, min(0.99, new_theta)), 4)
