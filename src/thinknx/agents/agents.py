from crewai import Agent
from typing import Optional, Any
from thinknx.config import settings
from thinknx.agents.tools import (
    web_search,
    web_scraper,
    arxiv_search,
    hn_search,
    query_user_knowledge,
    add_concept_to_graph,
    get_user_knowledge_gaps
)


def create_researcher_agent(llm: Optional[Any] = None) -> Agent:
    return Agent(
        role="Senior Technical Researcher",
        goal="Discover high-signal documentation, academic foundations, and community discussions on {topic}.",
        backstory=(
            "You are a meticulous technical analyst who systematically explores technical literature, "
            "official documentation, arXiv research papers, and engineer discussions on Hacker News. "
            "You prioritize primary documentation, concrete architectural patterns, and reproducible code."
        ),
        tools=[web_search, web_scraper, arxiv_search, hn_search],
        llm=llm or settings.crewai_llm_model,
        verbose=True,
        memory=True,
    )


def create_analyst_agent(llm: Optional[Any] = None) -> Agent:
    return Agent(
        role="Knowledge Graph Analyst",
        goal="Map concepts onto the Neo4j knowledge graph, verifying prerequisites and identifying knowledge gaps.",
        backstory=(
            "You are a cognitive knowledge architect and graph theory expert. You view human mastery as a "
            "directed acyclic graph where foundational concepts unlock advanced topics. You query Neo4j "
            "to inspect current mastery and structure new prerequisite edges."
        ),
        tools=[query_user_knowledge, add_concept_to_graph, get_user_knowledge_gaps],
        llm=llm or settings.crewai_llm_model,
        verbose=True,
        memory=True,
    )


def create_teacher_agent(llm: Optional[Any] = None) -> Agent:
    return Agent(
        role="Adaptive Master Educator",
        goal="Synthesize complex distributed systems and algorithms into intuitive analogies and clear code remarks.",
        backstory=(
            "You are a world-class educator and principal engineer. You teach by bridging new concepts "
            "to what the learner already understands. You separate code mechanics from architectural intent, "
            "providing annotated code remarks and terminal execution traces."
        ),
        tools=[query_user_knowledge],
        llm=llm or settings.crewai_llm_model,
        verbose=True,
        memory=True,
    )


def create_composer_agent(llm: Optional[Any] = None) -> Agent:
    return Agent(
        role="Curriculum Editor",
        goal="Assemble research, knowledge topology, and teaching modules into a polished, actionable lesson guide.",
        backstory=(
            "You are an executive editor for technical publications. You ensure content is concise, "
            "structured, scannable, and directly connected to practical implementation."
        ),
        tools=[],
        llm=llm or settings.crewai_llm_model,
        verbose=True,
        memory=False,
    )


def create_optimizer_agent(llm: Optional[Any] = None) -> Agent:
    return Agent(
        role="Spaced Repetition & Retention Specialist",
        goal="Optimize FSRS review intervals and evaluate user retention across connected concepts.",
        backstory=(
            "You are an expert in cognitive memory science and the FSRS spaced repetition algorithm. "
            "You examine quiz metrics and retrievability probabilities to reinforce learning gaps."
        ),
        tools=[query_user_knowledge, add_concept_to_graph, get_user_knowledge_gaps],
        llm=llm or settings.crewai_llm_model,
        verbose=True,
    )
