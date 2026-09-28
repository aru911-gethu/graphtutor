from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from thinknx.learning.explainer import AdaptiveExplainer
from thinknx.learning.engine import slugify
from thinknx.graph.driver import get_driver
import thinknx.graph.queries as graph_queries

router = APIRouter(tags=["Interactive WebApp Canvas"])

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
explainer = AdaptiveExplainer()


@router.get("/lesson/{topic}", response_class=HTMLResponse, summary="Serve interactive Telegram WebApp lesson")
async def view_lesson(
    request: Request,
    topic: str,
    uid: Optional[str] = Query(None, description="Telegram User ID, e.g. 'telegram:123456'"),
    level: str = Query("surface", description="Explanation level: surface, working, deep"),
):
    clean_topic = topic.replace("-", " ").strip().title()
    domain = "general"

    known_concepts = []
    if uid:
        driver = get_driver()
        try:
            async with driver.session() as session:
                user_concepts = await graph_queries.get_user_concepts(session, user_id=uid)
                known_concepts = [c["displayName"] for c in user_concepts if c.get("mastery", 0.0) >= 0.5]
                matching = [c for c in user_concepts if c["concept"] == slugify(topic)]
                if matching and matching[0].get("domain"):
                    domain = matching[0]["domain"]
        except Exception:
            pass

    payload = await explainer.generate_lesson_payload(
        concept=clean_topic,
        domain=domain,
        level=level,
        known_concepts=known_concepts,
    )

    return templates.TemplateResponse(
        request,
        "lesson_view.html",
        {
            "payload": payload,
            "user_id": uid,
        }
    )


@router.get("/canvas/{user_id}", summary="Get user knowledge graph as JSON")
async def view_graph_canvas(user_id: str) -> Dict[str, Any]:
    driver = get_driver()
    async with driver.session() as session:
        subgraph = await graph_queries.get_user_subgraph(session, user_id)
    return {"user_id": user_id, **subgraph}
