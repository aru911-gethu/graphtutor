# graphtutor

**A personal adaptive learning agent.** Tell it what you want to understand; it maps the concepts and their prerequisites, teaches each one in the format that fits (code, systems, math, AI pipelines, trade-offs, debugging), quizzes you, and schedules reviews with FSRS spaced repetition. Use it from Telegram or the web app.

> Status: backend, Telegram bot, `/api/v1`, Next.js web app and assessment module are in place; deployment, auth decision and Docker for the web app are open. See [PLAN.md](PLAN.md).

## Features

- **Six lesson themes**: Code, Systems, Math, AI pipelines, Decisions/trade-offs, Debugging, each with its own visual layout.
- **Per-user knowledge graph** in Neo4j: prerequisites, related concepts, mastery per concept; visualised in the web app with Cytoscape.
- **FSRS spaced repetition**: review schedule stored on the graph edge.
- **Multi-modal ingestion**: text, URLs, images (Claude vision), audio, GitHub repos, feeds.
- **Assessment**: Bloom-level question bank, Elo-IRT ability estimate, skill states from Unseen to Mastered, shareable quiz challenges.
- **Channels**: Telegram bot with Mini App lessons, and a web app.

## Requirements

Python 3.12 + [uv](https://docs.astral.sh/uv/), Docker (Neo4j, Redis), Node 20 (web app), an Anthropic API key, a Telegram bot token (for the bot).

## Quick start

```bash
cp .env.example .env                     # add Neo4j, Telegram, Anthropic keys
docker compose up -d neo4j redis   # infrastructure only
uv sync
uv run uvicorn graphtutor.main:app --reload --port 8000     # API + docs at /docs
uv run python -m graphtutor.channels.telegram               # Telegram bot
cd web && npm install && npm run dev                     # web app on :3000
uv run pytest                                            # test suite
```

## Run everything in Docker

```bash
docker compose up --build                 # neo4j, redis, api :8000, web :3000
docker compose --profile bot up --build   # also start the Telegram bot (needs TELEGRAM_BOT_TOKEN)
```

Create the bot first in Telegram via @BotFather and put its token in `.env`.

## Configuration

All settings come from `.env` (see `.env.example`): `NEO4J_*`, `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `TELEGRAM_BOT_TOKEN`, `ANTHROPIC_API_KEY`, and model routing (`MODEL_EXTRACT`, `MODEL_TEACH`, `MODEL_COMPLEX`, `MODEL_VISION`).

## Project layout

```
src/graphtutor/   api/(v1) assessment/ channels/ graph/ ingest/ learning/ models/ schemas/ services/ store/
tests/         api, channels, graph, ingest, learning
web/           Next.js app (dashboard, graph, lessons, reviews, onboarding, settings)
```

Architecture and module map: [AGENTS.md](AGENTS.md). Roadmap: [PLAN.md](PLAN.md).

## Roadmap

Docker for the web app, auth (Clerk or JWT), hosted data services (Aura, Neon, Upstash), streaming lessons, deployment, then billing.

## License

MIT
