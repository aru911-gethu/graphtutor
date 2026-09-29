# PLAN — graphtutor (formerly thinknx)

> Read `AGENTS.md` first. This file is the source of truth for **what is done and what is next**. Update checkboxes and "Last updated" when work lands.

**Last updated:** 2026-09-29 · **Repo:** github.com/aru911-gethu/Thinkx (local is **6 commits ahead, unpushed**) · **Path:** `C:\Users\aru91\Documents\Workspace_AI\Projects_Vscode\graphtutor`

## 1. Purpose and use cases

An adaptive learning companion: it learns what you want to know, maps it as a prerequisite graph, teaches each concept in the best of six visual formats, and schedules reviews with spaced repetition. Doubles as a portfolio project (code must stay explainable).

| # | Use case | Entry point | Status |
|---|---|---|---|
| U1 | `/learn <topic>` in Telegram: themed lesson, quiz, graded answer, FSRS update | `channels/telegram.py` | done |
| U2 | Ingest knowledge from text, URL, image (Claude vision), audio, GitHub, feeds | `ingest/*`, `api/v1/ingest.py` | code present; audio/github/feeds lightly tested |
| U3 | Web app: landing, onboarding, dashboard, graph canvas (Cytoscape), lessons, review session, settings | `web/` | pages present (Phase 1b marked done in CLAUDE.md) |
| U4 | Assessment: question bank with Bloom levels, Elo-IRT ability, knowledge-space tagging, skill report, quiz challenge links | `assessment/`, `api/v1/assessment.py`, `web/.../challenge/[id]` | done (Phase 1c) |
| U5 | Guest demo session with pre-seeded graph | `api/v1/demo.py`, `learning/seed_lessons.py` | done |
| U6 | Billing (Free/Pro) | n/a | deferred (Phase 2) |

## 2. Tech stack

| Layer | Choice |
|---|---|
| Backend | Python 3.11+ (target 3.12), uv, hatchling, FastAPI, uvicorn, WebSocket, Jinja2 (Telegram Mini App page) |
| Bot | python-telegram-bot 21 |
| Graph | Neo4j 5 (async driver), NetworkX analytics |
| Spaced repetition | `fsrs` (card state stored on `KNOWS` edges as `card_json` + `due`) |
| Relational | SQLAlchemy 2 async + aiosqlite (dev); Postgres/Neon planned |
| Cache / KV | Redis; custom KV client for Hostinger KV2 (`store/kv.py`) |
| LLM | Anthropic Claude (Haiku 4.5 extraction/quiz, Sonnet 5 teaching/evaluation); model IDs in `.env` `MODEL_*` |
| Auth | JWT (python-jose/passlib), Telegram login verification; Clerk planned |
| Frontend | Next.js 14 App Router, React 18, Tailwind, Cytoscape (+cola), KaTeX, lucide |
| Tests | pytest, pytest-asyncio, pytest-cov (45 tests) |
| Infra | Dockerfile (API), docker-compose (neo4j, redis, api, telegram-bot) |

## 3. Architecture

```
Telegram ─► channels/telegram ─┐                     Next.js web/ ─► /api/v1/*
                               ▼                                   │
                     learning/engine ◄───────────────────────────── api/v1 (me, graph, lessons, reviews, path, ingest, assessment, demo)
   ingest/* ─► concepts ─► graph/ (Neo4j: Concept, User, REQUIRES, RELATED_TO, KNOWS{fsrs})
   learning/{explainer (6 themes), quiz, mastery (FSRS), paths}   assessment/{question_bank, irt, kst, tagging, report}
   store/{cache, kv}  services/{auth_service, telegram_auth}  models/{user, session}  database.py (SQLite/Postgres)
```

## 4. Done

- [x] Phase 0: 7 blocking bugs fixed (imports, lesson shape, quiz grading, FSRS persistence, CORS/dev-token, model IDs); dead deps removed
- [x] Phase 1b: `/api/v1` (me, graph, lessons, reviews, path, ingest, demo) + Next.js pages (dashboard, graph, ingest, onboarding, review, settings, lesson/[slug], challenge/[id])
- [x] Phase 1c: assessment module (IRT, KST, tagging, report, question bank) + API
- [x] 45 tests across api, channels, graph, ingest, learning
- [x] Dockerfile + compose for API, bot, neo4j, redis
- [x] 2026-09-29: compose no longer references removed `graphtutor.worker`; `.python-version` (3.12) and `.dockerignore` added

## 5. Backlog (ordered)

| ID | Pri | Task | Where | Done when |
|---|---|---|---|---|
| TX-01 | P0 | Recreate `.env` (0 bytes after OneDrive sync) from `.env.example` | `.env` | app boots (user fills secrets) |
| TX-02 | P0 | Push the 6 local commits | git | `origin/main` up to date |
| TX-03 | P0 | Recreate `.venv`: `uv sync --reinstall`; rebuild web: `npm ci && npm run build` (clears OneDrive paths in `.next`) | root, `web/` | tests + build green |
| TX-04 | done | Renamed to graphtutor (package, compose, web, docs) 2026-09-29. Pending: rename GitHub repo `Thinkx`. **No Telegram bot has been created yet**: create `@graphtutor_bot` in BotFather | GitHub, BotFather | bot token in `.env` |
| TX-05 | P0 | Fix stale text: CLAUDE.md "Current state" said no frontend; replaced by AGENTS.md pointer (done this session) | docs | done |
| TX-06 | P1 | Align Python floor: `requires-python >=3.11` vs ruff `py312` vs docs 3.12 | `pyproject.toml` | one value |
| TX-07 | done | Docker: multi-stage API image (non-root, healthcheck, editable install), `web/Dockerfile` (Next standalone), `compose.yaml` (neo4j, redis, api, web, bot profile), `.dockerignore`s (2026-09-29) | `Dockerfile`, `web/Dockerfile`, `compose.yaml` | `docker compose up --build` serves web:3000 + api:8000 (verified 2026-09-29: both images build, API `/health` reports Neo4j + Redis connected, web returns 200) |
| TX-08 | P1 | Auth decision: Clerk (planned) vs current JWT; implement one path end to end | `api/v1/auth_deps.py`, `web/` | logged-in user sees own graph |
| TX-09 | P1 | Hosted data plan: AuraDB Free + Neon Postgres + Upstash; env-only switch | `config.py`, `database.py` | staging deploy works |
| TX-10 | P1 | Test gaps: `ingest/{audio,github,feeds,vision}`, `assessment/*` edge cases, `store/kv`, web e2e smoke (Playwright) | `tests/` | each package covered |
| TX-11 | P1 | Streaming lessons over SSE (`?stream=1`) | `api/v1/lessons.py` | first token < 2 s in web |
| TX-12 | P2 | Mermaid + Shiki rendering in lessons (planned in stack, not in `package.json`) | `web/` | code + diagram themes render |
| TX-13 | P2 | Rate limiting for guest demo | `api/v1/demo.py`, Redis | limit enforced |
| TX-14 | P2 | Deploy: Vercel (web) + Fly/Render (api, bot) | infra | public URL |
| TX-15 | P2 | Billing (Stripe or Lemon Squeezy) | new | deferred |

## 6. Structure gaps and target layout

Gaps: root `Dockerfile`/compose only cover the API; no `web/Dockerfile`; `api/` has both legacy (`auth, lesson, progress, ws`) and `v1/` routers; `models/` (ORM) vs `schemas/` naming is fine; `data/` ignored wholesale.

Target layout:

```
graphtutor/
├── pyproject.toml uv.lock .python-version .env.example .gitignore .dockerignore
├── README.md PLAN.md AGENTS.md CLAUDE.md(pointer) 
├── Dockerfile compose.yaml
├── src/graphtutor/  main.py config.py database.py  api/(v1/, legacy telegram-miniapp routes) assessment/ channels/ graph/ ingest/ learning/ models/ schemas/ services/ store/ templates/
├── tests/            mirrors src/
├── web/              Next.js (Dockerfile, .env.example)
└── docs/             architecture.md, api.md, deployment.md
```

Docker-readiness: API and bot share one image (different `command`); Neo4j and Redis are compose services; SQLite volume for dev; `web` gets its own image; all config from env.

## 7. Naming (decided)

**graphtutor**: says what it is (a tutor built on a knowledge graph) and matches how people search ("knowledge graph tutor", "adaptive learning graph"). Free on PyPI (checked 2026-09-29). Suggested GitHub description: "Adaptive learning agent: prerequisite knowledge graph in Neo4j, six lesson themes, FSRS spaced repetition, Telegram + web". Topics: `adaptive-learning`, `knowledge-graph`, `neo4j`, `spaced-repetition`, `fsrs`, `telegram-bot`, `fastapi`, `nextjs`. Docker note: the compose project prefix follows the folder name, so existing local Docker volumes from the old name (`thinknx_neo4j_data`, ...) will not be reused; new empty volumes are created.

## 8. Decisions log

- Claude-only LLM; model tiers by task (cheap extraction, strong teaching).
- Per-user Neo4j graph; FSRS state stored on the edge so a review is one graph write.
- Removed CrewAI, Celery, sentence-transformers, PyVis to keep the install light (2026-09).
- Web canvas uses Cytoscape client-side instead of server-rendered PyVis.
