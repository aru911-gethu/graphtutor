# CLAUDE.md — thinknx Development Guidelines

## Project Overview
`thinknx` is a personal adaptive learning agent delivered via Telegram bot and mobile WebApp canvases. It ingests multimodal content, maps concepts into a per-user Neo4j knowledge graph, adapts explanations to user proficiency across 6 foundational learning themes, quizzes to verify comprehension, and tracks retention using the FSRS spaced repetition algorithm.

## Tech Stack
- **Language**: Python 3.12+ (uv-managed)
- **API Framework**: FastAPI >= 0.115, Uvicorn, Jinja2 Templates
- **Bot Framework**: python-telegram-bot >= 21.0
- **Knowledge Graph**: Neo4j 5.x (official async driver `neo4j>=5.25`)
- **Spaced Repetition**: FSRS algorithm (`fsrs>=4.0`)
- **Relational DB**: SQLAlchemy 2.0 (asyncio) + aiosqlite
- **Task Queue / Cache**: Celery 5.4 + Redis 7.x
- **LLMs**: Anthropic Claude (Haiku for extraction/quizzes, Sonnet for teaching/evaluation/vision), OpenAI Whisper (audio)
- **Graph Analytics & Viz**: NetworkX 3.4, PyVis 0.3, sentence-transformers 3.3

## 6 Foundational Learning Themes
1. **Code & Implementation** (The Builder): Syntax-highlighted code + separate line remarks + terminal output.
2. **Systems, Infra & Protocols** (The Architect): Topology diagram + data journey steps + CLI + split-brain mode.
3. **Mathematical Foundations** (The Theorist): KaTeX formula hero + symbol glossary chips + geometric intuition.
4. **AI Models & Tensor Pipelines** (The ML Engineer): Tensor shape flow + attention heatmap + hyperparameters.
5. **Paradigms, Decisions & Trade-Offs** (The Decision Maker): Trade-off comparison matrix + decision tree + case study.
6. **Debugging & Diagnostics** (The Troubleshooter): Error log banner + root cause + before/after diff + checklist.

## Common Commands
```bash
# Install dependencies
uv sync --link-mode=copy

# Run FastAPI development server
uv run uvicorn thinknx.main:app --reload --port 8000

# Run Telegram bot worker
uv run python -m thinknx.channels.telegram

# Run Celery worker
uv run celery -A thinknx.worker worker -l info

# Run tests
uv run pytest
```
