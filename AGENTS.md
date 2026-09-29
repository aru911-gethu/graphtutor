# AGENTS.md — graphtutor (formerly thinknx; context file for AI assistants)

Read this and `PLAN.md`; avoid re-scanning the tree. Update the module index and PLAN.md checkboxes with every structural or status change. (`CLAUDE.md` is a pointer to this file.)

**Owner note:** Arun must be able to explain every part. Keep code clean and readable, not over-engineered; explain decisions. Build large files step by step. **Never read `.env`** (API keys): tell the user what to add.

## Commands (project root)

```bash
cp .env.example .env                                   # user fills secrets
docker compose up -d neo4j redis          # or the full stack: docker compose up --build
uv sync
uv run uvicorn graphtutor.main:app --reload --port 8000   # API, docs at /docs
uv run python -m graphtutor.channels.telegram             # bot
uv run pytest                                          # 45 tests; -x -v to stop on first failure
cd web && npm install && npm run dev                   # web on :3000
```

## Domain model

- **Six lesson themes** (`schemas/lesson.py` `LearningTheme`): CODE, SYSTEMS, MATH, AI_PIPELINE, DECISIONS, DEBUGGING. Each concept is classified into one; it decides layout and question style.
- **FSRS**: power-law forgetting `R = (1 + 0.235 t/S)^-0.5`; ratings 1 Again, 2 Hard, 3 Good, 4 Easy; card state persisted as `card_json` + `due` on KNOWS edges; mastery derived from stability, difficulty and last rating.
- **Neo4j**: `(:Concept {name, displayName, domain, complexity})`, `(:User {userId})`, `(:Concept)-[:REQUIRES]->(:Concept)`, `[:RELATED_TO]`, `(:User)-[:KNOWS {mastery, stability, difficulty, retrievability, depth, due, cardJson}]->(:Concept)`.
- **Learning flow**: `/learn topic` -> `LearningEngine.teach()` finds/creates concept -> `AdaptiveExplainer` calls Claude -> bot sends markdown + Mini App link -> shuffled quiz -> grade -> `FSRSMastery.record_review()` -> failure calls `propagate_failure()` up the prerequisite chain.
- **Assessment** (`assessment/`): Bloom-level question bank, Elo-IRT ability (separate from FSRS retention), KST tagging, skill states Unseen -> Exposed -> Recognizes -> Applies -> Explains -> Mastered.

## Module index (`src/graphtutor/`)

| Path | Purpose |
|---|---|
| `main.py`, `config.py`, `database.py` | app factory + CORS + routers, settings (`MODEL_*` IDs), async DB |
| `api/{auth,lesson,progress,ws,router}.py` | legacy routes: JWT/dev-token (dev only), lesson HTML view for Telegram Mini App, progress + graph JSON, WebSocket |
| `api/v1/{me,graph,lessons,reviews,path,ingest,assessment,demo,auth_deps,router}.py` | versioned JSON API used by `web/` |
| `assessment/{question_bank,irt,kst,tagging,report,models}.py` | Phase 1c |
| `channels/{base,router,telegram}.py` | channel abstraction, Telegram handlers (telegram.py 486 lines) |
| `graph/{driver,schema,queries,algorithms}.py` | Neo4j driver, seed schema, Cypher, PageRank/gaps/paths/communities |
| `ingest/{router,text,vision,audio,feeds,github}.py` | concept extraction per input type |
| `learning/{engine,explainer,mastery,paths,quiz,seed_lessons}.py` | teach loop, themed lesson generation, FSRS, paths, quizzes, cached demo lessons |
| `models/{user,session}.py`, `schemas/{lesson,user}.py` | ORM and pydantic |
| `services/{auth_service,telegram_auth}.py` | password/JWT, Telegram login verification |
| `store/{cache,kv}.py` | LLM response cache (`get_json/set_json`), KV2 client |
| `templates/lesson_view.html` | Mini App lesson page |

`web/src/app/`: `page.tsx` (landing), `dashboard`, `graph`, `ingest`, `onboarding`, `review`, `settings`, `lesson/[slug]`, `challenge/[id]`; `web/src/lib/{api,utils}.ts`. Tests: `tests/{test_api,test_channels,test_graph,test_ingest,test_learning}` + `conftest.py`.

## Known gotchas

- `.env` is empty right now (recreate from `.env.example`).
- Docker: `compose.yaml` runs neo4j, redis, api (:8000), web (:3000); the bot is behind `--profile bot`. `NEXT_PUBLIC_API_URL` is baked into the web image at build time.
- Local branch is 6 commits ahead of `origin/main`.
- Renamed from thinknx on 2026-09-29. **No Telegram bot exists yet**: create `@graphtutor_bot` in BotFather and put the token in `.env` as `TELEGRAM_BOT_TOKEN`. GitHub repo is still `Thinkx`.
- `.venv` and `web/.next` hold old OneDrive paths until `uv sync --reinstall` / `npm run build`.
- `pyproject` requires Python >=3.11 but ruff and docs assume 3.12.
- Worker/Celery was removed on purpose; do not re-add compose services that reference `graphtutor.worker`.
- Mermaid and Shiki were planned but are not in `web/package.json`.
