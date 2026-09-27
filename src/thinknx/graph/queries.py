from typing import List, Dict, Any, Optional
from neo4j import AsyncSession


async def create_user(session: AsyncSession, user_id: str, name: str, platform: str = "telegram") -> Dict[str, Any]:
    """Create a new user node in Neo4j. user_id format: 'telegram:123456' or 'slack:W123'"""
    query = """
    MERGE (u:User {userId: $userId})
    ON CREATE SET u.name = $name, u.platform = $platform,
                  u.explanationLevel = 'beginner', u.createdAt = datetime()
    RETURN u {.*} AS user
    """
    result = await session.run(query, userId=user_id, name=name, platform=platform)
    record = await result.single()
    return record["user"] if record else {}


async def get_user_concepts(session: AsyncSession, user_id: str) -> List[Dict[str, Any]]:
    """Get all concepts a user knows with mastery and FSRS data."""
    query = """
    MATCH (u:User {userId: $userId})-[k:KNOWS]->(c:Concept)
    RETURN c.name AS concept, c.displayName AS displayName, c.domain AS domain,
           c.complexity AS complexity,
           k.mastery AS mastery, k.stability AS stability, k.difficulty AS difficulty,
           k.retrievability AS retrievability, k.depth AS depth,
           toString(k.lastReview) AS lastReview, k.reviewCount AS reviewCount,
           k.explanationsThatWorked AS explanationsThatWorked
    ORDER BY k.mastery ASC
    """
    result = await session.run(query, userId=user_id)
    records = await result.data()
    return records


async def add_user_concept(
    session: AsyncSession,
    user_id: str,
    concept_name: str,
    mastery: float = 0.0,
    depth: str = "surface"
) -> Dict[str, Any]:
    """Add a concept to user's knowledge graph with initial FSRS parameters."""
    query = """
    MATCH (u:User {userId: $userId})
    MATCH (c:Concept {name: $conceptName})
    MERGE (u)-[k:KNOWS]->(c)
    ON CREATE SET k.mastery = $mastery, k.stability = 0.4, k.difficulty = 0.3,
                  k.retrievability = 1.0, k.depth = $depth,
                  k.lastReview = datetime(), k.reviewCount = 0,
                  k.explanationsThatWorked = []
    RETURN c {.*} AS concept, k {.*} AS knows
    """
    result = await session.run(query, userId=user_id, conceptName=concept_name, mastery=mastery, depth=depth)
    record = await result.single()
    return dict(record) if record else {}


async def update_mastery(
    session: AsyncSession,
    user_id: str,
    concept_name: str,
    mastery: float,
    stability: float,
    difficulty: float,
    retrievability: float,
    rating: int,
    depth: Optional[str] = None
) -> None:
    """Update FSRS parameters after a review and log the review event."""
    query = """
    MATCH (u:User {userId: $userId})-[k:KNOWS]->(c:Concept {name: $conceptName})
    SET k.mastery = $mastery, k.stability = $stability, k.difficulty = $difficulty,
        k.retrievability = $retrievability, k.lastReview = datetime(),
        k.reviewCount = coalesce(k.reviewCount, 0) + 1
    SET k.depth = CASE WHEN $depth IS NOT NULL THEN $depth ELSE k.depth END
    WITH u, c
    CREATE (u)-[:REVIEWED {
        timestamp: datetime(), rating: $rating, quizScore: $mastery
    }]->(c)
    """
    await session.run(
        query,
        userId=user_id,
        conceptName=concept_name,
        mastery=mastery,
        stability=stability,
        difficulty=difficulty,
        retrievability=retrievability,
        rating=rating,
        depth=depth
    )


async def propagate_failure(
    session: AsyncSession,
    user_id: str,
    failed_concept: str,
    decay_factor: float = 0.8
) -> None:
    """When user fails a concept, reduce retrievability of downstream dependent concepts."""
    query = """
    MATCH (u:User {userId: $userId})-[k:KNOWS]->(failed:Concept {name: $failedConcept})
    MATCH (failed)<-[:REQUIRES]-(dependent:Concept)
    MATCH (u)-[dk:KNOWS]->(dependent)
    SET dk.retrievability = dk.retrievability * $decayFactor
    """
    await session.run(query, userId=user_id, failedConcept=failed_concept, decayFactor=decay_factor)


async def get_due_reviews(
    session: AsyncSession,
    user_id: str,
    desired_retention: float = 0.9,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Get concepts due for review (retrievability below desired threshold)."""
    query = """
    MATCH (u:User {userId: $userId})-[k:KNOWS]->(c:Concept)
    WHERE k.retrievability < $desiredRetention
    RETURN c.name AS concept, c.displayName AS displayName,
           k.mastery AS mastery, k.retrievability AS retrievability,
           toString(k.lastReview) AS lastReview
    ORDER BY k.retrievability ASC
    LIMIT $limit
    """
    result = await session.run(query, userId=user_id, desiredRetention=desired_retention, limit=limit)
    return await result.data()


async def get_next_topics(session: AsyncSession, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Suggest next concepts: prerequisites met, not yet mastered."""
    query = """
    MATCH (u:User {userId: $userId})
    OPTIONAL MATCH (u)-[k:KNOWS]->(mastered:Concept)
    WHERE k.mastery >= 0.7
    WITH u, collect(mastered) AS masteredList
    MATCH (next:Concept)
    WHERE NOT next IN masteredList
      AND NOT EXISTS { MATCH (u)-[:KNOWS]->(next) WHERE true }
      AND ALL(prereq IN [(next)-[:REQUIRES]->(p) | p] WHERE prereq IN masteredList)
    RETURN next.name AS concept, next.displayName AS displayName,
           next.domain AS domain, next.complexity AS complexity
    ORDER BY next.complexity ASC
    LIMIT $limit
    """
    result = await session.run(query, userId=user_id, limit=limit)
    records = await result.data()
    if not records:
        # Fallback if no prerequisites mastered: return starter concepts (those with 0 prerequisites)
        fallback_query = """
        MATCH (c:Concept)
        WHERE NOT (c)-[:REQUIRES]->()
        RETURN c.name AS concept, c.displayName AS displayName,
               c.domain AS domain, c.complexity AS complexity
        ORDER BY c.complexity ASC
        LIMIT $limit
        """
        fb_result = await session.run(fallback_query, limit=limit)
        records = await fb_result.data()
    return records


async def get_learning_path(session: AsyncSession, user_id: str, goal_concept: str) -> List[Dict[str, Any]]:
    """Get ordered learning path from foundational prerequisites to goal concept."""
    query = """
    MATCH (u:User {userId: $userId})
    OPTIONAL MATCH (u)-[k:KNOWS]->(mastered:Concept)
    WHERE k.mastery >= 0.7
    WITH u, collect(mastered) AS masteredList

    MATCH (goal:Concept {name: $goalConcept})
    MATCH path = (goal)-[:REQUIRES*0..]->(prereq:Concept)
    WITH prereq, masteredList, length(path) AS depth
    WHERE NOT prereq IN masteredList
    RETURN DISTINCT prereq.name AS concept, prereq.displayName AS displayName,
           prereq.complexity AS complexity, depth
    ORDER BY depth DESC, prereq.complexity ASC
    """
    result = await session.run(query, userId=user_id, goalConcept=goal_concept)
    return await result.data()


async def get_knowledge_gaps(session: AsyncSession, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Concepts the user knows poorly — low mastery."""
    query = """
    MATCH (u:User {userId: $userId})-[k:KNOWS]->(c:Concept)
    WHERE k.mastery < 0.5
    RETURN c.name AS concept, c.displayName AS displayName,
           c.complexity AS complexity, k.mastery AS mastery,
           k.retrievability AS retrievability
    ORDER BY (c.complexity - k.mastery) DESC
    LIMIT $limit
    """
    result = await session.run(query, userId=user_id, limit=limit)
    return await result.data()


async def get_user_stats(session: AsyncSession, user_id: str) -> Dict[str, Any]:
    """Dashboard stats: total concepts, mastered, in-progress, gaps, reviews this week."""
    query = """
    MATCH (u:User {userId: $userId})
    OPTIONAL MATCH (u)-[k:KNOWS]->(c:Concept)
    WITH u,
         count(c) AS totalConcepts,
         sum(CASE WHEN k.mastery >= 0.8 THEN 1 ELSE 0 END) AS mastered,
         sum(CASE WHEN k.mastery >= 0.3 AND k.mastery < 0.8 THEN 1 ELSE 0 END) AS inProgress,
         sum(CASE WHEN k.mastery < 0.3 THEN 1 ELSE 0 END) AS gaps
    OPTIONAL MATCH (u)-[r:REVIEWED]->(c2:Concept)
    WHERE r.timestamp > datetime() - duration('P7D')
    WITH totalConcepts, mastered, inProgress, gaps, count(r) AS reviewsThisWeek
    RETURN coalesce(totalConcepts, 0) AS totalConcepts,
           coalesce(mastered, 0) AS mastered,
           coalesce(inProgress, 0) AS inProgress,
           coalesce(gaps, 0) AS gaps,
           coalesce(reviewsThisWeek, 0) AS reviewsThisWeek
    """
    result = await session.run(query, userId=user_id)
    record = await result.single()
    if record:
        return dict(record)
    return {"totalConcepts": 0, "mastered": 0, "inProgress": 0, "gaps": 0, "reviewsThisWeek": 0}


async def create_or_get_concept(
    session: AsyncSession,
    name: str,
    display_name: str,
    domain: str,
    complexity: float = 0.5,
    description: str = ""
) -> Dict[str, Any]:
    """Create a concept if it doesn't exist (for dynamic concept extraction)."""
    query = """
    MERGE (c:Concept {name: $name})
    ON CREATE SET c.displayName = $displayName, c.domain = $domain,
                  c.complexity = $complexity, c.description = $description,
                  c.createdAt = datetime()
    RETURN c {.*} AS concept
    """
    result = await session.run(
        query,
        name=name,
        displayName=display_name,
        domain=domain,
        complexity=complexity,
        description=description
    )
    record = await result.single()
    return record["concept"] if record else {}


async def get_user_subgraph(session: AsyncSession, user_id: str) -> Dict[str, Any]:
    """Extract user's active concept subgraph and prerequisites for PyVis/canvas visualization."""
    query = """
    MATCH (u:User {userId: $userId})-[k:KNOWS]->(c:Concept)
    OPTIONAL MATCH (c)-[r:REQUIRES]->(p:Concept)
    OPTIONAL MATCH (c)-[rel:RELATED_TO]->(rc:Concept)
    RETURN collect(DISTINCT c {.*, mastery: k.mastery, depth: k.depth}) AS nodes,
           collect(DISTINCT {source: c.name, target: p.name, type: 'REQUIRES'}) AS reqEdges,
           collect(DISTINCT {source: c.name, target: rc.name, type: 'RELATED_TO'}) AS relEdges
    """
    result = await session.run(query, userId=user_id)
    record = await result.single()
    if not record:
        return {"nodes": [], "edges": []}

    nodes = record["nodes"] or []
    edges = [e for e in (record["reqEdges"] or []) if e["target"] is not None]
    edges.extend([e for e in (record["relEdges"] or []) if e["target"] is not None])
    return {"nodes": nodes, "edges": edges}
