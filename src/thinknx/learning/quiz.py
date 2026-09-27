import json
from typing import List, Dict, Any, Optional
import structlog
from thinknx.config import settings

logger = structlog.get_logger(__name__)

QUIZ_PROMPT = """Generate {count} high-quality quiz questions about "{concept}" for a student at {level} level.

Student's current knowledge context: {mastery_context}

Return a valid JSON array of objects conforming to this schema:
[
  {{
    "question": "Question testing conceptual understanding and mental model",
    "type": "multiple_choice",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A",
    "explanation": "Brief explanation of why this answer is correct."
  }}
]

Rules:
- Questions MUST test UNDERSTANDING and edge cases, not rote memorization.
- Difficulty should match student's level ({level}).
- Return ONLY valid JSON, no markdown code fence or prose.
"""

EVALUATE_PROMPT = """Evaluate the student's answer to the quiz question.

Question: {question}
Expected Answer: {correct_answer}
Student's Answer: {student_answer}

Return a valid JSON object conforming to this schema:
{{
  "correct": true or false,
  "score": 0.0 to 1.0,
  "feedback": "Encouraging explanation connecting the concept to their answer.",
  "fsrs_rating": 1 to 4
}}

Rating guidelines:
1 = Again (incorrect or fundamental misunderstanding)
2 = Hard (partially correct or significant hints needed)
3 = Good (correct with appropriate reasoning)
4 = Easy (instantly correct, complete mastery)

Return ONLY valid JSON.
"""


class QuizGenerator:
    """Generates adaptive quiz questions and evaluates user answers using Anthropic Claude."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.anthropic_api_key
        self._client = None

    @property
    def client(self):
        if self._client is None and self.api_key:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except Exception as e:
                logger.warning("Failed to initialize Anthropic client", error=str(e))
        return self._client

    async def generate(
        self,
        concept: str,
        level: str = "working",
        count: int = 2,
        mastery_context: str = "new concept"
    ) -> List[Dict[str, Any]]:
        """Generate multiple-choice or short-answer quiz questions."""
        prompt = QUIZ_PROMPT.format(
            count=count,
            concept=concept,
            level=level,
            mastery_context=mastery_context
        )

        if self.client:
            try:
                resp = await self.client.messages.create(
                    model=settings.model_extract,
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = resp.content[0].text.strip()
                # Clean potential markdown fences
                if text.startswith("```"):
                    text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                parsed = json.loads(text)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed
            except Exception as e:
                logger.warning("Anthropic quiz generation error, using fallback", error=str(e))

        # Fallback realistic quiz questions
        return [
            {
                "question": f"What is the primary core advantage or mechanism of {concept}?",
                "type": "multiple_choice",
                "options": [
                    f"It provides structured abstraction and reduces failure modes in production.",
                    f"It guarantees O(1) constant time across all computational operations.",
                    f"It replaces all underlying storage and compute without trade-offs.",
                    f"It operates exclusively on offline single-threaded CPU architectures."
                ],
                "correct_answer": f"It provides structured abstraction and reduces failure modes in production.",
                "explanation": f"{concept} structures architectural complexity while maintaining reliability."
            },
            {
                "question": f"When implementing {concept}, which common trade-off or pitfall must be managed?",
                "type": "multiple_choice",
                "options": [
                    "Memory overhead and latency vs. consistency requirements.",
                    "Complete lack of debugging visibility across any logging pipeline.",
                    "Incompatibility with any standard networking protocols.",
                    "Strict requirement for manual bytecode manipulation."
                ],
                "correct_answer": "Memory overhead and latency vs. consistency requirements.",
                "explanation": "Every architectural paradigm requires balancing performance against resource utilization."
            }
        ][:count]

    async def evaluate_answer(
        self,
        question: str,
        correct_answer: str,
        student_answer: str
    ) -> Dict[str, Any]:
        """Evaluate a student's answer and assign an FSRS rating (1-4)."""
        prompt = EVALUATE_PROMPT.format(
            question=question,
            correct_answer=correct_answer,
            student_answer=student_answer
        )

        if self.client:
            try:
                resp = await self.client.messages.create(
                    model=settings.model_teach,
                    max_tokens=400,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = resp.content[0].text.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                data = json.loads(text)
                return {
                    "correct": bool(data.get("correct", False)),
                    "score": float(data.get("score", 0.5)),
                    "feedback": str(data.get("feedback", "")),
                    "fsrs_rating": int(data.get("fsrs_rating", 3 if data.get("correct") else 1)),
                }
            except Exception as e:
                logger.warning("Anthropic answer evaluation error, using heuristic", error=str(e))

        # Heuristic fallback matching
        is_exact = student_answer.strip().lower() == correct_answer.strip().lower()
        is_partial = any(token in correct_answer.lower() for token in student_answer.lower().split() if len(token) > 3)

        if is_exact:
            return {
                "correct": True,
                "score": 1.0,
                "feedback": "Spot on! That accurately captures the core principle.",
                "fsrs_rating": 4
            }
        elif is_partial:
            return {
                "correct": True,
                "score": 0.8,
                "feedback": "Correct! You identified the essential mechanism.",
                "fsrs_rating": 3
            }
        else:
            return {
                "correct": False,
                "score": 0.2,
                "feedback": f"Not quite. The expected answer is: '{correct_answer}'.",
                "fsrs_rating": 1
            }
