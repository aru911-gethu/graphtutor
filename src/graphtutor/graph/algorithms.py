from typing import List, Dict, Any, Optional
import networkx as nx


def _get_simple_digraph(G: nx.MultiDiGraph) -> nx.DiGraph:
    """Flatten a MultiDiGraph into a weighted simple DiGraph."""
    simple = nx.DiGraph()
    for n, attrs in G.nodes(data=True):
        simple.add_node(n, **attrs)
    for u, v, data in G.edges(data=True):
        w = data.get("strength", data.get("weight", 1.0))
        if simple.has_edge(u, v):
            simple[u][v]["weight"] = simple[u][v].get("weight", 1.0) + float(w)
        else:
            simple.add_edge(u, v, weight=float(w))
    return simple


def build_networkx_from_subgraph(subgraph: Dict[str, Any]) -> nx.MultiDiGraph:
    """Build a NetworkX MultiDiGraph from Neo4j subgraph dictionary {nodes, edges}."""
    G = nx.MultiDiGraph()
    for node in subgraph.get("nodes", []):
        node_id = node.get("name") or node.get("id")
        if node_id:
            G.add_node(
                node_id,
                name=node.get("displayName") or node.get("name") or node_id,
                domain=node.get("domain", "General"),
                category=node.get("domain", "General"),
                complexity=node.get("complexity", 0.5),
                mastery=node.get("mastery", 0.0),
                user_familiarity=node.get("mastery", 0.0),
                depth=node.get("depth", "surface"),
                type="concept"
            )

    for edge in subgraph.get("edges", []):
        src = edge.get("source")
        tgt = edge.get("target")
        rel_type = edge.get("type", "REQUIRES")
        if src and tgt:
            G.add_edge(src, tgt, key=rel_type, strength=1.0)

    return G


def rank_concepts(G: nx.MultiDiGraph) -> List[Dict[str, Any]]:
    """Compute PageRank scores for concepts to highlight foundational hubs."""
    if len(G) == 0:
        return []

    simple = _get_simple_digraph(G)
    try:
        ranks = nx.pagerank(simple, alpha=0.85, weight="weight")
    except Exception:
        ranks = {n: 1.0 / len(G) for n in G.nodes()}

    results = []
    for node_id, score in sorted(ranks.items(), key=lambda x: x[1], reverse=True):
        attrs = G.nodes.get(node_id, {})
        familiarity = attrs.get("user_familiarity", attrs.get("mastery", 0.0))
        results.append({
            "key": node_id,
            "name": attrs.get("name", node_id),
            "category": attrs.get("category", "General"),
            "pagerank": round(score, 4),
            "complexity": attrs.get("complexity", 0.5),
            "user_familiarity": familiarity,
        })
    return results


def find_communities(G: nx.MultiDiGraph) -> List[List[str]]:
    """Identify concept clusters/domains using Louvain modularity."""
    if len(G) < 2:
        return [[n] for n in G.nodes()]

    undirected = _get_simple_digraph(G).to_undirected()
    try:
        from networkx.algorithms.community import louvain_communities
        communities = louvain_communities(undirected, seed=42)
    except Exception:
        from networkx.algorithms.community import greedy_modularity_communities
        communities = greedy_modularity_communities(undirected)

    return [sorted(list(c)) for c in communities]


def find_knowledge_gaps(G: nx.MultiDiGraph, threshold: float = 0.4) -> List[Dict[str, Any]]:
    """Concepts with high structural importance (PageRank) but low mastery."""
    ranks = rank_concepts(G)
    gaps = []
    for item in ranks:
        familiarity = item.get("user_familiarity", 0.0)
        if familiarity < threshold:
            gap_severity = item["pagerank"] * (1.0 - familiarity)
            gaps.append({
                **item,
                "gap_severity": round(gap_severity, 4),
                "recommendation": "High priority prerequisite to study"
            })
    return sorted(gaps, key=lambda x: x["gap_severity"], reverse=True)


def find_learning_path(G: nx.MultiDiGraph, from_concept: str, to_concept: str) -> List[str]:
    """Find topological/shortest prerequisite traversal path between two concepts."""
    if from_concept not in G or to_concept not in G:
        return []

    simple = _get_simple_digraph(G)
    try:
        path = nx.shortest_path(simple, source=from_concept, target=to_concept)
        return path
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        # Check reverse in case edge points from dependent to prerequisite
        try:
            rev_path = nx.shortest_path(simple, source=to_concept, target=from_concept)
            return list(reversed(rev_path))
        except Exception:
            return []
