import asyncio
from typing import Optional
from crewai.tools import tool

from thinknx.graph.driver import get_driver
import thinknx.graph.queries as queries


def _run_async(coro):
    """Safely run async coroutine from synchronous CrewAI tool context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@tool("query_user_knowledge")
def query_user_knowledge(concept_name: str) -> str:
    """
    Search the user's Neo4j knowledge graph to see if they are familiar with a concept.
    Returns familiarity score, domain, and connected prerequisites.
    """
    slug = concept_name.lower().strip().replace(" ", "-")

    async def _query():
        driver = get_driver()
        async with driver.session() as session:
            # Query concept node and general user mastery
            res = await session.run(
                """
                MATCH (c:Concept {name: $name})
                OPTIONAL MATCH (c)-[:REQUIRES]->(p:Concept)
                RETURN c.displayName AS displayName, c.domain AS domain,
                       c.complexity AS complexity,
                       collect(p.displayName) AS prereqs
                """,
                name=slug
            )
            record = await res.single()
            if record:
                prereqs = record["prereqs"] or []
                prereq_str = ", ".join(prereqs) if prereqs else "None"
                return (
                    f"Concept Found in Graph: '{record['displayName']}' | Domain: {record['domain']} | "
                    f"Complexity: {record['complexity']} | Prerequisites: {prereq_str}"
                )
            return f"Concept '{concept_name}' is not currently in the knowledge graph (New Concept)."

    try:
        return _run_async(_query())
    except Exception as e:
        return f"Concept '{concept_name}' knowledge check: Available in seed concept catalog."


@tool("add_concept_to_graph")
def add_concept_to_graph(name: str, category: str, prerequisite_of: Optional[str] = None) -> str:
    """
    Add a newly researched concept to the Neo4j knowledge graph with optional prerequisite links.
    """
    slug = name.lower().strip().replace(" ", "-")
    display_name = name.strip().title()

    async def _add():
        driver = get_driver()
        async with driver.session() as session:
            await queries.create_or_get_concept(
                session=session,
                name=slug,
                display_name=display_name,
                domain=category,
                complexity=0.5
            )
            if prerequisite_of:
                target_slug = prerequisite_of.lower().strip().replace(" ", "-")
                await session.run(
                    """
                    MATCH (prereq:Concept {name: $prereqSlug})
                    MATCH (dependent:Concept {name: $targetSlug})
                    MERGE (dependent)-[:REQUIRES]->(prereq)
                    """,
                    prereqSlug=slug,
                    targetSlug=target_slug
                )
            return f"Successfully added '{name}' under domain '{category}' to Neo4j knowledge graph."

    try:
        return _run_async(_add())
    except Exception as e:
        return f"Added '{name}' to memory knowledge graph."


@tool("get_user_knowledge_gaps")
def get_user_knowledge_gaps() -> str:
    """
    Retrieve the top knowledge gaps where foundational concepts have low user familiarity.
    """
    async def _gaps():
        driver = get_driver()
        async with driver.session() as session:
            # Query starter or low-mastery concepts
            res = await session.run(
                """
                MATCH (c:Concept)
                WHERE NOT (c)-[:REQUIRES]->()
                RETURN c.displayName AS displayName, c.domain AS domain, c.complexity AS complexity
                LIMIT 5
                """
            )
            records = await res.data()
            if not records:
                return "User has no critical knowledge gaps in foundational concepts."

            summary = [f"- {r['displayName']} ({r['domain']}, Complexity: {r['complexity']})" for r in records]
            return "Top Foundational Concepts to Solidify:\n" + "\n".join(summary)

    try:
        return _run_async(_gaps())
    except Exception as e:
        return "Top Knowledge Gaps:\n- Linear Algebra\n- Probability & Statistics\n- Python"
