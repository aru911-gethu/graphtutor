from pathlib import Path
from typing import Union, Optional, Dict, Any
import networkx as nx
from pyvis.network import Network

from thinknx.config import settings

NODE_COLORS = {
    "concept": {"background": "#3B82F6", "border": "#1D4ED8", "highlight": "#60A5FA"},
    "math": {"background": "#8B5CF6", "border": "#6D28D9", "highlight": "#A78BFA"},
    "ai-ml": {"background": "#06B6D4", "border": "#0891B2", "highlight": "#67E8F9"},
    "programming": {"background": "#10B981", "border": "#059669", "highlight": "#34D399"},
    "databases": {"background": "#F59E0B", "border": "#D97706", "highlight": "#FCD34D"},
    "devops": {"background": "#EC4899", "border": "#DB2777", "highlight": "#F472B6"},
    "web-dev": {"background": "#6366F1", "border": "#4F46E5", "highlight": "#818CF8"},
}

DEFAULT_COLOR = {"background": "#64748B", "border": "#475569", "highlight": "#94A3B8"}


def export_interactive_html(
    G: nx.MultiDiGraph,
    output_path: Optional[Union[str, Path]] = None,
    height: str = "100vh",
    width: str = "100%",
    open_browser: bool = False
) -> str:
    """Renders a full-screen, mobile-friendly interactive PyVis graph."""
    target_path = Path(output_path) if output_path else settings.graph_dir / "user_knowledge_graph.html"
    target_path.parent.mkdir(parents=True, exist_ok=True)

    net = Network(
        height=height,
        width=width,
        directed=True,
        notebook=False,
        bgcolor="#0B0F19",
        font_color="#F8FAFC"
    )

    net.barnes_hut(
        gravity=-2800,
        central_gravity=0.25,
        spring_length=110,
        spring_strength=0.05,
        damping=0.09,
        overlap=0
    )

    for node_id, data in G.nodes(data=True):
        domain = str(data.get("domain", data.get("category", "concept"))).lower()
        color_scheme = NODE_COLORS.get(domain, DEFAULT_COLOR)
        label = data.get("name", node_id)
        short_label = label[:20] + "..." if len(label) > 20 else label

        mastery = float(data.get("mastery", data.get("user_familiarity", 0.0)))
        depth = data.get("depth", "surface")
        size = 18 + int(mastery * 14)

        tooltip = (
            f"<div style='font-family:system-ui,-apple-system,sans-serif;padding:8px;background:#1E293B;color:#F8FAFC;border-radius:6px;'>"
            f"<b style='color:#60A5FA;font-size:14px;'>{label}</b><br/>"
            f"<span style='color:#94A3B8;font-size:12px;'>Domain: {domain}</span><br/>"
            f"<span style='font-size:12px;'>Mastery: {int(mastery * 100)}% ({depth.capitalize()})</span>"
            f"</div>"
        )

        net.add_node(
            node_id,
            label=short_label,
            title=tooltip,
            color=color_scheme,
            size=size,
            shape="dot",
            font={"size": 13, "color": "#F8FAFC", "face": "system-ui"}
        )

    for u, v, k, data in G.edges(keys=True, data=True):
        edge_type = str(k)
        edge_color = "#38BDF8" if edge_type == "REQUIRES" else "#64748B"
        dashed = edge_type == "RELATED_TO"

        net.add_edge(
            u,
            v,
            title=f"Relation: {edge_type}",
            color=edge_color,
            width=2.0 if edge_type == "REQUIRES" else 1.0,
            arrows="to",
            dashes=dashed
        )

    net.write_html(str(target_path))
    with open(target_path, "r", encoding="utf-8") as f:
        return f.read()
