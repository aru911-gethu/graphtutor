from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import HTMLResponse
from typing import Dict, Any, List

from thinknx.graph.driver import get_driver
import thinknx.graph.queries as queries
from thinknx.graph.algorithms import build_networkx_from_subgraph
from thinknx.graph.visualizer import export_interactive_html

router = APIRouter(prefix="/progress", tags=["Progress & Knowledge Graph"])


@router.get("/{user_id}", summary="Get user mastery stats and known concepts")
async def get_user_progress(user_id: str) -> Dict[str, Any]:
    """Returns aggregated mastery counts and concept list for dashboard."""
    driver = get_driver()
    async with driver.session() as session:
        stats = await queries.get_user_stats(session, user_id)
        concepts = await queries.get_user_concepts(session, user_id)

    return {
        "user_id": user_id,
        "stats": stats,
        "concepts": concepts,
    }


@router.get("/{user_id}/visualize", response_class=HTMLResponse, summary="Serve interactive knowledge graph HTML")
async def visualize_user_graph(user_id: str):
    """Pulls user's Neo4j knowledge subgraph into NetworkX and returns interactive PyVis HTML."""
    driver = get_driver()
    async with driver.session() as session:
        subgraph = await queries.get_user_subgraph(session, user_id)

    G = build_networkx_from_subgraph(subgraph)
    html_content = export_interactive_html(G)
    return HTMLResponse(content=html_content)


@router.get("/{user_id}/gaps", summary="Get user knowledge gaps")
async def get_user_gaps(user_id: str, limit: int = 10) -> Dict[str, Any]:
    """Concepts with low mastery requiring spaced repetition or review."""
    driver = get_driver()
    async with driver.session() as session:
        gaps = await queries.get_knowledge_gaps(session, user_id, limit=limit)
    return {"user_id": user_id, "gaps": gaps}


@router.get("/{user_id}/next", summary="Suggest next topics based on prerequisites")
async def get_user_next_topics(user_id: str, limit: int = 5) -> Dict[str, Any]:
    """Concepts ready for study whose prerequisites are met."""
    driver = get_driver()
    async with driver.session() as session:
        topics = await queries.get_next_topics(session, user_id, limit=limit)
    return {"user_id": user_id, "suggestions": topics}


@router.get("/{user_id}/path", summary="Compute learning path to goal")
async def get_path_to_goal(
    user_id: str,
    goal: str = Query(..., description="Target concept name (e.g. transformers or ai-agents)")
) -> Dict[str, Any]:
    """Returns ordered prerequisite traversal to target goal."""
    driver = get_driver()
    async with driver.session() as session:
        path = await queries.get_learning_path(session, user_id, goal)
    return {"user_id": user_id, "goal": goal, "path": path}
