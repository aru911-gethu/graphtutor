from neo4j import AsyncDriver
import structlog

logger = structlog.get_logger(__name__)

CONSTRAINTS = [
    """
    CREATE CONSTRAINT user_unique IF NOT EXISTS
    FOR (u:User) REQUIRE u.userId IS UNIQUE
    """,
    """
    CREATE CONSTRAINT concept_name_unique IF NOT EXISTS
    FOR (c:Concept) REQUIRE c.name IS UNIQUE
    """
]

INDEXES = [
    "CREATE INDEX user_id_idx IF NOT EXISTS FOR (u:User) ON (u.userId)",
    "CREATE INDEX concept_name_idx IF NOT EXISTS FOR (c:Concept) ON (c.name)",
    "CREATE INDEX concept_domain_idx IF NOT EXISTS FOR (c:Concept) ON (c.domain)",
    "CREATE INDEX source_url_idx IF NOT EXISTS FOR (s:Source) ON (s.url)",
]

SEED_CONCEPTS_QUERY = """
MERGE (la:Concept {name: "linear-algebra"})
ON CREATE SET la.displayName = "Linear Algebra", la.domain = "math", la.complexity = 0.4, la.createdAt = datetime()

MERGE (calc:Concept {name: "calculus"})
ON CREATE SET calc.displayName = "Calculus", calc.domain = "math", calc.complexity = 0.4, calc.createdAt = datetime()

MERGE (prob:Concept {name: "probability"})
ON CREATE SET prob.displayName = "Probability & Statistics", prob.domain = "math", prob.complexity = 0.4, prob.createdAt = datetime()

MERGE (ml:Concept {name: "machine-learning"})
ON CREATE SET ml.displayName = "Machine Learning", ml.domain = "ai-ml", ml.complexity = 0.5, ml.createdAt = datetime()

MERGE (dl:Concept {name: "deep-learning"})
ON CREATE SET dl.displayName = "Deep Learning", dl.domain = "ai-ml", dl.complexity = 0.6, dl.createdAt = datetime()

MERGE (nn:Concept {name: "neural-networks"})
ON CREATE SET nn.displayName = "Neural Networks", nn.domain = "ai-ml", nn.complexity = 0.6, nn.createdAt = datetime()

MERGE (att:Concept {name: "attention-mechanism"})
ON CREATE SET att.displayName = "Attention Mechanism", att.domain = "ai-ml", att.complexity = 0.7, att.createdAt = datetime()

MERGE (trans:Concept {name: "transformers"})
ON CREATE SET trans.displayName = "Transformers", trans.domain = "ai-ml", trans.complexity = 0.7, trans.createdAt = datetime()

MERGE (llm:Concept {name: "large-language-models"})
ON CREATE SET llm.displayName = "Large Language Models", llm.domain = "ai-ml", llm.complexity = 0.8, llm.createdAt = datetime()

MERGE (rag:Concept {name: "rag"})
ON CREATE SET rag.displayName = "Retrieval-Augmented Generation", rag.domain = "ai-ml", rag.complexity = 0.7, rag.createdAt = datetime()

MERGE (agents:Concept {name: "ai-agents"})
ON CREATE SET agents.displayName = "AI Agents", agents.domain = "ai-ml", agents.complexity = 0.8, agents.createdAt = datetime()

MERGE (kg:Concept {name: "knowledge-graphs"})
ON CREATE SET kg.displayName = "Knowledge Graphs", kg.domain = "databases", kg.complexity = 0.6, kg.createdAt = datetime()

MERGE (gt:Concept {name: "graph-theory"})
ON CREATE SET gt.displayName = "Graph Theory", gt.domain = "math", gt.complexity = 0.5, gt.createdAt = datetime()

MERGE (py:Concept {name: "python"})
ON CREATE SET py.displayName = "Python", py.domain = "programming", py.complexity = 0.3, py.createdAt = datetime()

MERGE (api:Concept {name: "rest-apis"})
ON CREATE SET api.displayName = "REST APIs", api.domain = "web-dev", api.complexity = 0.4, api.createdAt = datetime()

MERGE (docker:Concept {name: "docker"})
ON CREATE SET docker.displayName = "Docker & Containers", docker.domain = "devops", docker.complexity = 0.4, docker.createdAt = datetime()

// Prerequisites (Concept)-[:REQUIRES]->(Prerequisite)
MERGE (ml)-[:REQUIRES]->(la)
MERGE (ml)-[:REQUIRES]->(prob)
MERGE (ml)-[:REQUIRES]->(py)
MERGE (dl)-[:REQUIRES]->(ml)
MERGE (dl)-[:REQUIRES]->(calc)
MERGE (nn)-[:REQUIRES]->(dl)
MERGE (att)-[:REQUIRES]->(nn)
MERGE (trans)-[:REQUIRES]->(att)
MERGE (llm)-[:REQUIRES]->(trans)
MERGE (rag)-[:REQUIRES]->(llm)
MERGE (rag)-[:REQUIRES]->(kg)
MERGE (agents)-[:REQUIRES]->(llm)
MERGE (kg)-[:REQUIRES]->(gt)

// Related
MERGE (ml)-[:RELATED_TO]->(prob)
MERGE (dl)-[:RELATED_TO]->(nn)
MERGE (trans)-[:RELATED_TO]->(att)
MERGE (rag)-[:RELATED_TO]->(agents)
MERGE (kg)-[:RELATED_TO]->(rag)
"""


async def init_schema(driver: AsyncDriver) -> None:
    """Create constraints, indexes, and seed core AI/ML prerequisite concept DAG."""
    logger.info("Initializing Neo4j schema and seed concepts...")
    try:
        async with driver.session() as session:
            for constraint in CONSTRAINTS:
                try:
                    await session.run(constraint)
                except Exception as e:
                    logger.debug("Constraint creation notice", msg=str(e))

            for index in INDEXES:
                try:
                    await session.run(index)
                except Exception as e:
                    logger.debug("Index creation notice", msg=str(e))

            await session.run(SEED_CONCEPTS_QUERY)
            logger.info("Neo4j schema and seed concept DAG initialized successfully.")
    except Exception as e:
        logger.warning("Could not initialize Neo4j schema (DB may be offline or unreachable)", error=str(e))
