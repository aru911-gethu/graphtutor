# thinknx — Personal Adaptive Learning Agent

`thinknx` is a personal adaptive learning companion delivered through Telegram and mobile interactive WebApp canvases. It combines multi-modal knowledge ingestion, a per-user Neo4j knowledge graph, polymorphic teaching across 6 learning themes, and FSRS spaced repetition to help you master complex topics systematically.

---

## Key Features

- **Telegram Interface & In-App WebApp Canvases**: Seamless mobile learning via `@thinknx_bot` with rich inline keyboards, voice notes, photo inputs, and responsive visual canvases.
- **6 Foundational Polymorphic Themes**:
  1. **Code & Implementation**: Clean code blocks with separate line-by-line annotations and expected output.
  2. **Systems & Infrastructure**: Interactive topology diagrams, step-by-step data journeys, and failure modes.
  3. **Mathematical Foundations**: Crisp KaTeX formulas, de-greeking symbol glossaries, and geometric intuition.
  4. **AI Models & Tensor Pipelines**: Tensor dimensionality pipelines and matrix attention flows.
  5. **Paradigms & Trade-offs**: Side-by-side comparison matrices, decision trees, and case studies.
  6. **Debugging & Diagnostics**: Error log analysis, root cause anatomy, and before/after code diffs.
- **Per-User Knowledge Graph (Neo4j)**: Visualized prerequisite DAGs showing mastered topics, in-progress subjects, and knowledge gaps.
- **FSRS Spaced Repetition**: Modern Free Spaced Repetition Scheduler (`fsrs>=4.0`) that schedules reviews with 20-30% fewer reviews than SM-2.
- **Multi-Modal Ingestion**: Extract concepts from textbook photos, whiteboard diagrams, voice notes, technical articles, and GitHub repositories.

---

## Quickstart

### 1. Prerequisites
- Python 3.12+ and [uv](https://github.com/astral-sh/uv)
- Docker & Docker Compose (for Neo4j & Redis)

### 2. Environment Setup
```bash
cp .env.example .env
# Edit .env with your Neo4j, Telegram, and API keys
```

### 3. Start Infrastructure
```bash
docker compose up -d neo4j redis
```

### 4. Install Dependencies & Run App
```bash
uv sync --link-mode=copy
uv run uvicorn thinknx.main:app --reload --port 8000
```

### 5. Start the Telegram Bot
```bash
uv run python -m thinknx.channels.telegram
```

---

## License
MIT