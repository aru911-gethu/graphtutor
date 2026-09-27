from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from thinknx.learning.explainer import AdaptiveExplainer, detect_theme
from thinknx.learning.engine import slugify
from thinknx.graph.driver import get_driver
import thinknx.graph.queries as graph_queries
from thinknx.graph.visualizer import export_user_graph_html

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
    """
    Renders a polymorphic mobile-optimized HTML lesson tailored to one of the 6 foundational themes:
    Code, Systems, Math, AI Pipeline, Decisions, or Debugging.
    """
    clean_topic = topic.replace("-", " ").strip().title()
    domain = "general"

    # If user ID provided, retrieve known concepts from Neo4j
    known_concepts = []
    if uid:
        driver = get_driver()
        try:
            async with driver.session() as session:
                user_concepts = await graph_queries.get_user_concepts(session, user_id=uid)
                known_concepts = [c["displayName"] for c in user_concepts if c.get("mastery", 0.0) >= 0.5]
                concept_node = await graph_queries.get_concept(session, slugify(topic))
                if concept_node and "domain" in concept_node:
                    domain = concept_node["domain"]
        except Exception:
            pass

    # Generate structured lesson payload matching theme
    payload = await explainer.generate_lesson_payload(
        concept=clean_topic,
        domain=domain,
        level=level,
        known_concepts=known_concepts,
    )

    return templates.TemplateResponse(
        "lesson_view.html",
        {
            "request": request,
            "payload": payload,
            "user_id": uid,
        }
    )


@router.get("/canvas/{user_id}", response_class=HTMLResponse, summary="Serve interactive knowledge graph canvas")
async def view_graph_canvas(user_id: str):
    """Serve full-screen interactive node-link knowledge graph for Telegram WebApp."""
    driver = get_driver()
    async with driver.session() as session:
        html = await export_user_graph_html(session, user_id)
        return HTMLResponse(content=html)
