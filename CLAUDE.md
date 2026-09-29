# CLAUDE.md — thinknx

## What this is

thinknx is a personal adaptive learning agent. It extracts concepts from text, images, voice, and URLs; maps them into a per-user Neo4j prerequisite graph; teaches each concept using one of six visual themes; quizzes the learner; and schedules reviews with FSRS spaced repetition.

This is both a **user-testing MVP** and a **portfolio project**. Code should be clean, readable, and explainable — not over-engineered. The owner (Arun) needs to walk through and explain every part. Teach and explain decisions when building.

## Current state (as of 2026-09-29)

**Phase 0 complete** — 7 blocking bugs fixed, unused deps removed, 28/28 tests pass.

The app currently runs as a FastAPI backend + Telegram bot. There is no web frontend yet.

### What was fixed in Phase 0

| Bug | What | File |
|-----|------|------|
| B1 | Broken import — added `get_json`, `set_json`, `response_cache` singleton | `store/cache.py` |
| B2 | Wrong lesson shape — engine returns `{payload, chat_markdown}` now | `learning/engine.py`, `channels/telegram.py` |
| B3 | URL param mismatch — standardized on `uid=` | `channels/telegram.py`, `api/lesson.py` |
| B4 | Quiz grading fake — options now shuffled, correct index tracked | `channels/telegram.py` |
| B5 | FSRS never scheduled reviews — full Card state now persists as `card_json` + `due` on KNOWS edges | `learning/mastery.py`, `graph/queries.py` |
| B6 | Security — removed wildcard CORS, dev-token guarded by environment check | `main.py`, `api/auth.py` |
| B7 | Invalid model IDs — updated to valid Claude model IDs | `config.py` |

### What was removed

- `src/thinknx/agents/` — CrewAI multi-agent system (unused, pulled torch)
- `src/thinknx/worker.py` — Celery tasks (unused)
- `src/thinknx/graph/embeddings.py` — sentence-transformers (unused, GBs of deps)
- `src/thinknx/graph/visualizer.py` — PyVis server-side HTML (replaced by JSON endpoint)
- Dependencies: crewai, celery, openai, pyvis, scikit-learn, sentence-transformers, numpy

## Tech stack

### Current (backend only)

- **Language**: Python 3.12+ (uv-managed)
- **API**: FastAPI + Uvicorn + Jinja2 templates (for Telegram Mini App pages)
- **Bot**: python-telegram-bot >= 21.0
- **Knowledge graph**: Neo4j 5.x (async driver)
- **Spaced repetition**: FSRS algorithm (`fsrs>=4.0`)
- **Relational DB**: SQLAlchemy 2.0 (async) + aiosqlite (SQLite)
- **LLM**: Anthropic Claude only — Haiku 4.5 for extraction/quizzes, Sonnet 5 for teaching/evaluation
- **Graph analytics**: NetworkX 3.4

### Target MVP (Phase 1b)

- **Frontend**: Next.js (App Router) + Tailwind + shadcn/ui in `web/` folder
- **API**: FastAPI `/api/v1` with JSON + SSE streaming
- **Auth**: Clerk (free tier) — FastAPI verifies Clerk JWTs
- **Knowledge graph**: Neo4j AuraDB Free
- **Users/relational**: Postgres via Neon (free tier)
- **Cache/rate limiting**: Upstash Redis
- **Graph viz**: Cytoscape.js (client-side, replaces PyVis)
- **Lesson rendering**: KaTeX + Mermaid + Shiki (bundled, no CDN)
- **Deploy**: Vercel (web) + Fly.io or Render (API + bot) + Aura + Neon + Upstash

## Project structure

```
src/thinknx/
├── api/                  # FastAPI routes
│   ├── auth.py           # JWT auth, dev-token (dev only)
│   ├── health.py         # Health check
│   ├── lesson.py         # Lesson HTML view (Telegram Mini App)
│   ├── progress.py       # User progress + graph JSON endpoint
│   ├── router.py         # API router aggregation
│   └── ws.py             # WebSocket endpoint
├── channels/
│   ├── router.py         # Channel routing
│   └── telegram.py       # Telegram bot handlers (/start, /learn, /quiz, callbacks)
├── graph/
│   ├── algorithms.py     # PageRank, knowledge gaps, learning paths, communities
│   ├── driver.py         # Neo4j async driver singleton
│   ├── queries.py        # All Neo4j Cypher queries (user concepts, mastery, due reviews, subgraph)
│   └── schema.py         # Graph schema + seed concepts
├── ingest/
│   ├── router.py         # Ingestion routing (text, URL, image, voice)
│   ├── text.py           # Text concept extraction via Claude
│   └── vision.py         # Image concept extraction via Claude
├── learning/
│   ├── engine.py         # Main learning loop (teach, evaluate)
│   ├── explainer.py      # Adaptive lesson generation (6 themes) via Claude
│   ├── mastery.py        # FSRS spaced repetition (review, record_review, compute_retrievability)
│   ├── paths.py          # Learning path generation
│   └── quiz.py           # Quiz generation + evaluation via Claude
├── schemas/
│   └── lesson.py         # LessonPayload Pydantic model, LearningTheme enum (6 themes)
├── store/
│   └── cache.py          # LLM response cache (get_json, set_json)
├── templates/
│   └── lesson_view.html  # Jinja2 template for Telegram Mini App lesson page
├── config.py             # Settings (env vars, model IDs, CORS)
├── main.py               # FastAPI app factory, CORS, router mounting
└── models.py             # SQLAlchemy User model
```

## Key domain concepts

### Six learning themes (LearningTheme enum)

Each concept is classified into one theme, which determines the visual layout and question style:

1. **CODE** — syntax-highlighted code, line remarks, terminal output
2. **SYSTEMS** — topology diagrams, data journey steps, CLI examples
3. **MATH** — KaTeX formulas, symbol glossary, geometric intuition
4. **AI_PIPELINE** — tensor shape flow, attention heatmaps, hyperparameters
5. **DECISIONS** — trade-off matrices, decision trees, case studies
6. **DEBUGGING** — error logs, root cause analysis, before/after diffs

### FSRS spaced repetition

Power-law forgetting curve: `R = (1 + 0.235 · t/S)^-0.5`

- Card state persisted as `card_json` on Neo4j KNOWS edges
- `due` datetime drives review scheduling
- Ratings: 1 (Again), 2 (Hard), 3 (Good), 4 (Easy)
- `mastery` is derived from stability, difficulty, and latest rating

### Neo4j graph model

- `(:Concept {name, displayName, domain, complexity})` — knowledge nodes
- `(:User {userId})` — learner nodes
- `(:Concept)-[:REQUIRES]->(:Concept)` — prerequisite edges
- `(:Concept)-[:RELATED_TO]->(:Concept)` — related concept edges
- `(:User)-[:KNOWS {mastery, stability, difficulty, retrievability, depth, due, cardJson}]->(:Concept)` — per-user progress

### Learning flow

1. User sends `/learn <topic>` in Telegram
2. `LearningEngine.teach()` finds or creates the concept in Neo4j
3. `AdaptiveExplainer.generate_lesson_payload()` calls Claude to generate a themed lesson
4. Bot sends markdown summary + opens Mini App with full lesson
5. Quiz question presented with shuffled options
6. Answer graded → `FSRSMastery.record_review()` updates card state + due date
7. Failed concepts trigger `propagate_failure()` on prerequisite chain

## Common commands

```bash
# Install dependencies (use --link-mode=copy on OneDrive paths)
uv sync --link-mode=copy

# Run FastAPI dev server
uv run uvicorn thinknx.main:app --reload --port 8000

# Run Telegram bot
uv run python -m thinknx.channels.telegram

# Run tests
uv run pytest

# Run tests verbose with stop on first failure
uv run pytest -x -v
```

## Important notes

- **Never read .env files** — they contain API keys. If a key needs to be set, tell the user what to add and let them do it.
- **OneDrive warning** — this repo lives in OneDrive. OneDrive sync can replace files with 0-byte cloud placeholders. If files appear empty, run `git restore .` to recover from the last commit. The folder should be marked "Always keep on this device".
- **Build incrementally** — build large files/artifacts step by step across multiple tool calls, not in one giant write.
- Code should be **clean and explainable**, not over-engineered. This is a portfolio + learning project.

## Build plan

### Phase 0: Recover & stabilize — DONE ✓

All 7 bugs fixed, unused deps removed, 28/28 tests passing.

### Phase 1a: Visual evaluation report — DONE ✓

Published as artifact. Covers scorecard, architecture diagrams, bug audit, stack comparison, roadmap.

### Phase 1b: Showcase MVP web app — DONE ✓

- **API v1** (`src/thinknx/api/v1/`): All versioned endpoints operational (me, graph, lessons with SSE streaming, reviews, path, ingest, demo session, assessment).
- **Identity & Auth**: Clerk JWT, Local JWT, Telegram HMAC-SHA256, and Guest demo sessions.
- **Web app** (`web/`, Next.js 14 App Router + Tailwind): All 8 screens + Challenge comparison page built and passing `next build`.
- **Pre-cached Seed Lessons**: Instant zero-latency responses for the 16 core concepts across all 6 visual themes.

### Phase 1c: Assessment & skill tagging — DONE ✓

- **Question bank**: Linked to Bloom's taxonomy levels (remember -> create) and concept prerequisites.
- **Elo-IRT ability estimation**: Pelánek (2016) Rasch model tracking latent ability $\theta$ independently from FSRS retention.
- **KST propagation**: Knowledge Space Theory DAG evidence propagation and failure diagnostic probes.
- **Skill tags**: Deterministic mapping from ability and stability to Unseen -> Mastered.
- **State friction tags**: Blocker, Fragile, Misconception, Overconfident, Guessing, Rusty.
- **Skill report & challenges**: Radar chart domain competency and shareable `/challenge/{id}` links.

### Phase 2: Billing — DEFERRED

Stripe or Lemon Squeezy. Free/Pro tiers. Not in scope for MVP.
