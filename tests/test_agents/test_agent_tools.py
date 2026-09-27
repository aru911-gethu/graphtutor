import pytest
from thinknx.agents.tools import (
    web_search,
    web_scraper,
    arxiv_search,
    hn_search,
    query_user_knowledge,
    get_user_knowledge_gaps
)


def test_web_search_tool():
    """Verify web search tool returns results string."""
    res = web_search.run("Attention Mechanism in Transformers")
    assert isinstance(res, str)
    assert len(res) > 20


def test_arxiv_search_tool():
    """Verify arXiv search tool returns formatted paper summary."""
    res = arxiv_search.run("Knowledge Graphs")
    assert isinstance(res, str)
    assert len(res) > 20


def test_hn_search_tool():
    """Verify Hacker News search tool returns discussion links."""
    res = hn_search.run("Neo4j vector search")
    assert isinstance(res, str)
    assert len(res) > 20


def test_graph_tools_fallback():
    """Verify Neo4j graph tools execute or fallback gracefully."""
    res_query = query_user_knowledge.run("Transformers")
    assert isinstance(res_query, str)

    res_gaps = get_user_knowledge_gaps.run()
    assert isinstance(res_gaps, str)
