import json
import logging
import re
from typing import List, Optional, Dict, Any

from graphtutor.config import settings
from graphtutor.store.cache import response_cache
from graphtutor.schemas.lesson import (
    LearningTheme,
    LessonPayload,
    CodeRemark,
    MathSymbol,
    JourneyStep,
    TradeoffItem,
    DiffBlock,
)

logger = logging.getLogger(__name__)


def detect_theme(concept: str, domain: str = "general") -> LearningTheme:
    """Infer the appropriate learning theme from the concept name and domain category."""
    concept_lower = concept.lower()
    domain_lower = domain.lower()

    # Math
    if any(k in concept_lower or k in domain_lower for k in ["math", "calculus", "algebra", "probabilit", "bayes", "loss", "gradient", "eigen"]):
        return LearningTheme.MATH

    # AI & Data Pipelines
    if any(k in concept_lower or k in domain_lower for k in ["attention", "transformer", "rag", "embedding", "diffusion", "llm", "neural", "token", "lora"]):
        return LearningTheme.AI_PIPELINE

    # Systems, Infra & Protocols
    if any(k in concept_lower or k in domain_lower for k in ["git", "docker", "kubernetes", "k8s", "redis", "kafka", "tcp", "http", "grpc", "replicate", "raft", "infra", "devops"]):
        return LearningTheme.SYSTEMS

    # Debugging & Gotchas
    if any(k in concept_lower or k in domain_lower for k in ["debug", "leak", "oom", "deadlock", "error", "vulnerab", "bottleneck", "profil"]):
        return LearningTheme.DEBUGGING

    # Paradigms & Decisions
    if any(k in concept_lower or k in domain_lower for k in ["vs", "tradeoff", "monolith", "microservice", "solid", "pattern", "system-design", "architect"]):
        return LearningTheme.DECISIONS

    # Default to Code / Builder for programming and other technical concepts
    return LearningTheme.CODE


STRUCTURED_THEME_PROMPT = """You are an elite technical educator creating an interactive visual lesson for "{concept}" (Theme: {theme}).
Student level: {level}
Known concepts: {known_concepts}

Generate a valid JSON object strictly matching this schema for {theme}:
{{
  "concept_slug": "{slug}",
  "display_name": "{concept}",
  "theme": "{theme}",
  "summary": "2-sentence high-level overview",
  "intuition_anchor": "Intuitive real-world analogy grounded in everyday experience",

  // For 'code':
  "code_snippet": "10-12 lines of idiomatic code without boilerplate",
  "code_language": "python",
  "code_remarks": [{{"line": 2, "note": "Why this specific line matters"}}],
  "terminal_output": "Expected terminal output showing input -> result",

  // For 'systems':
  "topology_mermaid": "graph LR\\n A[Client] --> B[Load Balancer] --> C[Service]",
  "data_journey": [{{"step": 1, "title": "Staging", "state_description": "Data enters index"}}],
  "cli_commands": "$ git status\\n$ git commit -m 'update'",
  "failure_mode_gotcha": "Common trap or split-brain edge case",

  // For 'math':
  "formula_latex": "\\\\text{{Formula}}(x) = ...",
  "symbol_glossary": [{{"symbol": "x", "name": "Feature", "meaning": "Input variable"}}],
  "geometric_intuition": "Visual coordinate or curve intuition",

  // For 'ai_pipeline':
  "tensor_pipeline_steps": ["[Batch, Seq, Dim] -> [Batch, Heads, Dim]", "Apply Softmax"],
  "matrix_intuition": "Visual attention score distribution",
  "hyperparameters_note": "Key hyperparameter trade-offs",

  // For 'decisions':
  "tradeoff_matrix": [{{"dimension": "Latency", "option_a": "Fast (<10ms)", "option_b": "Slow (>200ms)"}}],
  "decision_tree_mermaid": "graph TD\\n A[Need Speed?] -->|Yes| B[Option A]\\n A -->|No| C[Option B]",
  "case_study": "How a tier-1 company chose between these approaches",

  // For 'debugging':
  "error_log": "Traceback or error message",
  "root_cause": "Anatomy of the bug",
  "code_diff": {{"before": "buggy_code()", "after": "fixed_code()", "explanation": "Why this fixes it"}},
  "prevention_checklist": ["Checklist item 1", "Checklist item 2"]
}}

Rules:
- Return ONLY valid JSON, no markdown code fences, no extra text.
- Fill only the fields relevant to theme '{theme}'. Keep explanations crisp, intuitive, and mobile-friendly."""


def clean_json_text(text: str) -> str:
    """Clean markdown code fences and whitespace from raw LLM output."""
    stripped = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", stripped)
    if match:
        return match.group(1).strip()
    return stripped


class AdaptiveExplainer:
    """Generates polymorphic visual lessons calibrated across 6 foundational learning themes."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.model_teach

    async def explain(
        self,
        concept: str,
        level: str = "surface",
        domain: str = "general",
        known_concepts: Optional[List[str]] = None,
        previous_analogies: Optional[List[str]] = None,
    ) -> str:
        """Produce markdown summary for chat interface."""
        payload = await self.generate_lesson_payload(
            concept=concept,
            domain=domain,
            level=level,
            known_concepts=known_concepts,
        )
        return self._format_chat_markdown(payload)

    async def generate_lesson_payload(
        self,
        concept: str,
        domain: str = "general",
        level: str = "surface",
        known_concepts: Optional[List[str]] = None,
    ) -> LessonPayload:
        """Generate structured lesson payload conforming to one of the 6 themes."""
        theme = detect_theme(concept, domain)
        slug = concept.lower().replace(" ", "-")
        known_str = ", ".join(known_concepts[:5]) if known_concepts else "None recorded"

        prompt = STRUCTURED_THEME_PROMPT.format(
            concept=concept,
            theme=theme.value,
            level=level,
            known_concepts=known_str,
            slug=slug,
        )

        cached = await response_cache.get_json(self.model, prompt)
        if cached and isinstance(cached, dict):
            try:
                return LessonPayload.model_validate(cached)
            except Exception:
                pass

        if self.api_key and not self.api_key.startswith("sk-ant-placeholder"):
            try:
                import anthropic
                client = anthropic.AsyncAnthropic(api_key=self.api_key)
                response = await client.messages.create(
                    model=self.model,
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw_text = clean_json_text(response.content[0].text)
                data = json.loads(raw_text)
                payload = LessonPayload.model_validate(data)
                await response_cache.set_json(self.model, prompt, data)
                return payload
            except Exception as e:
                logger.warning(f"Claude structured lesson call failed: {e}. Using deterministic fallback.")

        return self._build_fallback_payload(concept, domain, theme)

    def _format_chat_markdown(self, payload: LessonPayload) -> str:
        """Generate a concise, mobile-friendly markdown teaser for the Telegram chat."""
        theme_emojis = {
            LearningTheme.CODE: "💻",
            LearningTheme.SYSTEMS: "🏗️",
            LearningTheme.MATH: "📐",
            LearningTheme.AI_PIPELINE: "🧠",
            LearningTheme.DECISIONS: "⚖️",
            LearningTheme.DEBUGGING: "🛠️",
        }
        emoji = theme_emojis.get(payload.theme, "💡")

        lines = [
            f"{emoji} **{payload.display_name}** ({payload.theme.value.upper()})\n",
            f"_{payload.summary}_\n",
            f"**Intuition Anchor:**\n{payload.intuition_anchor}\n",
        ]

        if payload.theme == LearningTheme.CODE and payload.code_snippet:
            lines.append(f"```python\n{payload.code_snippet}\n```")
        elif payload.theme == LearningTheme.MATH and payload.formula_latex:
            lines.append(f"$$\n{payload.formula_latex}\n$$")
        elif payload.theme == LearningTheme.SYSTEMS and payload.cli_commands:
            lines.append(f"```bash\n{payload.cli_commands}\n```")
        elif payload.theme == LearningTheme.DEBUGGING and payload.error_log:
            lines.append(f"⚠️ *Gotcha:* {payload.root_cause or payload.error_log}")

        return "\n".join(lines)

    def _build_fallback_payload(self, concept: str, domain: str, theme: LearningTheme) -> LessonPayload:
        """Deterministic theme fallbacks for offline operation and automated testing."""
        slug = concept.lower().replace(" ", "-")

        if theme == LearningTheme.CODE:
            return LessonPayload(
                concept_slug=slug,
                display_name=concept,
                theme=LearningTheme.CODE,
                summary=f"Core algorithmic implementation of {concept}.",
                intuition_anchor=f"Think of {concept} as an automated factory conveyor routing dynamic tasks.",
                code_snippet=(
                    f"def process_{slug.replace('-', '_')}(data, threshold=0.5):\n"
                    f"    transformed = [x * 1.5 for x in data]\n"
                    f"    return [y for y in transformed if y > threshold]"
                ),
                code_language="python",
                code_remarks=[
                    CodeRemark(line=2, note="Scales raw data inputs uniformly."),
                    CodeRemark(line=3, note="Filters results based on threshold boundary."),
                ],
                terminal_output=">>> process([0.2, 0.4, 0.8])\n[0.6, 1.2]",
            )

        elif theme == LearningTheme.SYSTEMS:
            return LessonPayload(
                concept_slug=slug,
                display_name=concept,
                theme=LearningTheme.SYSTEMS,
                summary=f"Infrastructure architecture and data distribution in {concept}.",
                intuition_anchor="Like a parcel delivery tracking system where checkpoints record state handoffs.",
                topology_mermaid=(
                    "graph LR\n"
                    "  Client[Client / IDE] -->|push/commit| Stage[Staging Index]\n"
                    "  Stage -->|snapshot| Repo[Object DAG Repository]\n"
                    "  Repo -->|replicate| Remote[Remote Origin]"
                ),
                data_journey=[
                    JourneyStep(step=1, title="Working Directory", state_description="Unstaged changes in local workspace."),
                    JourneyStep(step=2, title="Staging Index", state_description="Prepared snapshot hashed via SHA-1."),
                    JourneyStep(step=3, title="Commit Object", state_description="Immutable graph node pointing to tree & parent."),
                ],
                cli_commands=f"$ {slug} status\n$ {slug} commit -m 'checkpoint'",
                failure_mode_gotcha="Detached state: committing without an active branch reference risks garbage collection.",
            )

        elif theme == LearningTheme.MATH:
            return LessonPayload(
                concept_slug=slug,
                display_name=concept,
                theme=LearningTheme.MATH,
                summary=f"Mathematical formulation and probability foundations of {concept}.",
                intuition_anchor="Updating confidence in a belief when fresh observable evidence is presented.",
                formula_latex=r"P(A|B) = \frac{P(B|A) P(A)}{P(B)}",
                symbol_glossary=[
                    MathSymbol(symbol="P(A|B)", name="Posterior", meaning="Updated probability of event A after seeing evidence B"),
                    MathSymbol(symbol="P(B|A)", name="Likelihood", meaning="Probability of observing evidence B if hypothesis A is true"),
                    MathSymbol(symbol="P(A)", name="Prior", meaning="Initial belief probability before seeing evidence"),
                ],
                geometric_intuition="Proportional partition area of overlapping probability spaces.",
            )

        elif theme == LearningTheme.AI_PIPELINE:
            return LessonPayload(
                concept_slug=slug,
                display_name=concept,
                theme=LearningTheme.AI_PIPELINE,
                summary=f"Vector transformation and representation flow in {concept}.",
                intuition_anchor="A high-dimensional library index where semantic meaning is distance.",
                tensor_pipeline_steps=[
                    "Raw Tokens: [Batch=2, Seq=128]",
                    "Dense Embeddings: [Batch=2, Seq=128, Dim=768]",
                    "Multi-Head Q/K/V Projections: [Batch=2, Heads=12, Seq=128, HeadDim=64]",
                    "Scaled Dot-Product Softmax: [Batch=2, Heads=12, Seq=128, Seq=128]",
                ],
                matrix_intuition="Self-attention heatmap showing bidirectional cross-token relevance.",
                hyperparameters_note="Temperature scales probability sharpness; Top-p bounds token candidates.",
            )

        elif theme == LearningTheme.DECISIONS:
            return LessonPayload(
                concept_slug=slug,
                display_name=concept,
                theme=LearningTheme.DECISIONS,
                summary=f"Architectural trade-offs and decision criteria for {concept}.",
                intuition_anchor="Choosing between a specialized sports car (speed) vs a minivan (capacity).",
                tradeoff_matrix=[
                    TradeoffItem(dimension="Latency", option_a="Sub-5ms (In-Memory)", option_b="50-100ms (Distributed Disk)"),
                    TradeoffItem(dimension="Cost", option_a="High RAM cost", option_b="Low storage cost"),
                    TradeoffItem(dimension="Consistency", option_a="Strong Consistency", option_b="Eventual Consistency"),
                ],
                decision_tree_mermaid=(
                    "graph TD\n"
                    "  A[Real-time <10ms?] -->|Yes| B[Option A: In-Memory]\n"
                    "  A -->|No| C[Option B: Distributed]"
                ),
                case_study="Netflix adopted asynchronous event-driven queues to avoid cascading synchronous failures.",
            )

        else:  # DEBUGGING
            return LessonPayload(
                concept_slug=slug,
                display_name=concept,
                theme=LearningTheme.DEBUGGING,
                summary=f"Root-cause diagnosis and resolution for {concept}.",
                intuition_anchor="Finding a slow leak in a pressurized pipe before the system overheats.",
                error_log="CUDA out of memory. Tried to allocate 2.40 GiB (GPU 0; 8.00 GiB total capacity)",
                root_cause="Accumulated computational graphs across training iterations without zeroing gradients.",
                code_diff=DiffBlock(
                    before="loss = model(inputs)\ntotal_loss += loss  # Keeps graph alive!",
                    after="loss = model(inputs)\ntotal_loss += loss.item()  # Detaches tensor scalar",
                    explanation="loss.item() converts tensor to Python float, allowing GC to free activations.",
                ),
                prevention_checklist=[
                    "Always call loss.item() when tracking metrics over loops.",
                    "Use torch.no_grad() during inference and evaluation.",
                ],
            )
