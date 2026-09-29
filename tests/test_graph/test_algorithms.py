import pytest
import networkx as nx
from graphtutor.graph.algorithms import (
    rank_concepts,
    find_knowledge_gaps,
    find_learning_path,
    find_communities,
    build_networkx_from_subgraph
)


@pytest.fixture
def sample_graph():
    """Create a sample multi-node knowledge DAG."""
    G = nx.MultiDiGraph()
    G.add_node("math", name="Linear Algebra", domain="math", mastery=0.9, complexity=0.4, type="concept")
    G.add_node("ml", name="Machine Learning", domain="ai-ml", mastery=0.3, complexity=0.5, type="concept")
    G.add_node("dl", name="Deep Learning", domain="ai-ml", mastery=0.1, complexity=0.6, type="concept")

    G.add_edge("dl", "ml", key="REQUIRES", strength=1.0)
    G.add_edge("ml", "math", key="REQUIRES", strength=1.0)
    return G


def test_rank_concepts(sample_graph):
    """Verify PageRank computation ranks foundational prerequisites."""
    ranks = rank_concepts(sample_graph)
    assert len(ranks) == 3
    # Math is pointed to by ML and DL, so it should have highest or significant rank
    keys = [r["key"] for r in ranks]
    assert "math" in keys


def test_find_knowledge_gaps(sample_graph):
    """Verify detection of concepts with low mastery."""
    gaps = find_knowledge_gaps(sample_graph, threshold=0.4)
    gap_keys = [g["key"] for g in gaps]
    assert "dl" in gap_keys
    assert "ml" in gap_keys
    assert "math" not in gap_keys  # mastery is 0.9 >= 0.4


def test_find_learning_path(sample_graph):
    """Verify topological learning path resolution."""
    path = find_learning_path(sample_graph, "dl", "math")
    assert path == ["dl", "ml", "math"]


def test_build_networkx_from_subgraph():
    """Verify conversion from Neo4j subgraph dict to NetworkX graph."""
    subgraph = {
        "nodes": [
            {"name": "attention", "displayName": "Attention Mechanism", "domain": "ai-ml", "mastery": 0.5},
            {"name": "transformers", "displayName": "Transformers", "domain": "ai-ml", "mastery": 0.2}
        ],
        "edges": [
            {"source": "transformers", "target": "attention", "type": "REQUIRES"}
        ]
    }
    G = build_networkx_from_subgraph(subgraph)
    assert len(G.nodes) == 2
    assert len(G.edges) == 1
    assert G.has_edge("transformers", "attention")
