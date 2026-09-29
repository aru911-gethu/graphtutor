from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from graphtutor.api.v1.auth_deps import get_current_user_v1
from graphtutor.models.user import User
from graphtutor.graph.driver import get_driver
from graphtutor.graph.queries import get_user_subgraph

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])

FALLBACK_NODES = [
    {"name": "linear-algebra", "displayName": "Linear Algebra", "domain": "math", "complexity": 0.4, "mastery": 0.85},
    {"name": "calculus", "displayName": "Calculus", "domain": "math", "complexity": 0.4, "mastery": 0.75},
    {"name": "probability", "displayName": "Probability & Statistics", "domain": "math", "complexity": 0.4, "mastery": 0.70},
    {"name": "python", "displayName": "Python", "domain": "programming", "complexity": 0.3, "mastery": 0.90},
    {"name": "machine-learning", "displayName": "Machine Learning", "domain": "ai-ml", "complexity": 0.5, "mastery": 0.65},
    {"name": "deep-learning", "displayName": "Deep Learning", "domain": "ai-ml", "complexity": 0.6, "mastery": 0.60},
    {"name": "neural-networks", "displayName": "Neural Networks", "domain": "ai-ml", "complexity": 0.6, "mastery": 0.55},
    {"name": "attention-mechanism", "displayName": "Attention Mechanism", "domain": "ai-ml", "complexity": 0.7, "mastery": 0.40},
    {"name": "transformers", "displayName": "Transformers", "domain": "ai-ml", "complexity": 0.7, "mastery": 0.35},
    {"name": "large-language-models", "displayName": "Large Language Models", "domain": "ai-ml", "complexity": 0.8, "mastery": 0.20},
    {"name": "graph-theory", "displayName": "Graph Theory", "domain": "math", "complexity": 0.5, "mastery": 0.50},
    {"name": "knowledge-graphs", "displayName": "Knowledge Graphs", "domain": "databases", "complexity": 0.6, "mastery": 0.45},
    {"name": "rag", "displayName": "Retrieval-Augmented Generation", "domain": "ai-ml", "complexity": 0.7, "mastery": 0.25},
    {"name": "ai-agents", "displayName": "AI Agents", "domain": "ai-ml", "complexity": 0.8, "mastery": 0.15},
    {"name": "rest-apis", "displayName": "REST APIs", "domain": "web-dev", "complexity": 0.4, "mastery": 0.80},
    {"name": "docker", "displayName": "Docker & Containers", "domain": "devops", "complexity": 0.4, "mastery": 0.60},
]

FALLBACK_EDGES = [
    {"source": "linear-algebra", "target": "machine-learning", "type": "REQUIRES"},
    {"source": "probability", "target": "machine-learning", "type": "REQUIRES"},
    {"source": "python", "target": "machine-learning", "type": "REQUIRES"},
    {"source": "calculus", "target": "deep-learning", "type": "REQUIRES"},
    {"source": "machine-learning", "target": "deep-learning", "type": "REQUIRES"},
    {"source": "deep-learning", "target": "neural-networks", "type": "REQUIRES"},
    {"source": "neural-networks", "target": "attention-mechanism", "type": "REQUIRES"},
    {"source": "attention-mechanism", "target": "transformers", "type": "REQUIRES"},
    {"source": "transformers", "target": "large-language-models", "type": "REQUIRES"},
    {"source": "large-language-models", "target": "rag", "type": "REQUIRES"},
    {"source": "graph-theory", "target": "knowledge-graphs", "type": "REQUIRES"},
    {"source": "knowledge-graphs", "target": "rag", "type": "REQUIRES"},
    {"source": "large-language-models", "target": "ai-agents", "type": "REQUIRES"},
]


def format_cytoscape(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, Any]:
    cy_nodes = []
    mastered_count = 0
    learning_count = 0
    locked_count = 0

    for n in nodes:
        slug = n.get("name") or n.get("id") or n.get("concept")
        display_name = n.get("displayName") or n.get("display_name") or slug.replace("-", " ").title()
        domain = n.get("domain", "general")
        mastery = float(n.get("mastery", 0.0))
        complexity = float(n.get("complexity", 0.5))
        retrievability = float(n.get("retrievability", 1.0))

        if mastery >= 0.8:
            status = "mastered"
            mastered_count += 1
        elif retrievability < 0.6 and mastery > 0.2:
            status = "decaying"
            learning_count += 1
        elif mastery >= 0.2:
            status = "learning"
            learning_count += 1
        else:
            status = "locked"
            locked_count += 1

        size = int(32 + (complexity * 24))

        cy_nodes.append({
            "data": {
                "id": slug,
                "label": display_name,
                "domain": domain,
                "mastery": round(mastery, 2),
                "theta": round(mastery, 2),
                "complexity": round(complexity, 2),
                "status": status,
                "size": size
            }
        })

    cy_edges = []
    for idx, e in enumerate(edges):
        src = e.get("source")
        tgt = e.get("target")
        edge_type = e.get("type", "REQUIRES")
        if src and tgt:
            cy_edges.append({
                "data": {
                    "id": f"e_{src}_{tgt}_{idx}",
                    "source": src,
                    "target": tgt,
                    "label": edge_type
                }
            })

    return {
        "elements": {
            "nodes": cy_nodes,
            "edges": cy_edges
        },
        "summary": {
            "total_nodes": len(cy_nodes),
            "mastered": mastered_count,
            "learning": learning_count,
            "locked": locked_count
        }
    }


@router.get("", response_model=Dict[str, Any])
async def get_user_graph(current_user: User = Depends(get_current_user_v1)):
    try:
        driver = get_driver()
        async with driver.session() as session:
            subgraph = await get_user_subgraph(session, current_user.id)
            nodes = subgraph.get("nodes", [])
            edges = subgraph.get("edges", [])
            if nodes:
                return format_cytoscape(nodes, edges)
    except Exception:
        pass

    return format_cytoscape(FALLBACK_NODES, FALLBACK_EDGES)
