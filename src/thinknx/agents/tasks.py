from crewai import Task, Agent
from typing import List


def create_research_task(agent: Agent, topic: str, depth: str = "working") -> Task:
    return Task(
        description=(
            f"Conduct technical research on the topic: '{topic}'.\n"
            "1. Search web documentation and articles for core architectural concepts.\n"
            "2. Search arXiv for mathematical foundations and algorithmic papers.\n"
            "3. Search Hacker News for engineering trade-offs, gotchas, and production lessons.\n"
            "4. Extract concrete code implementations, key equations, and common pitfalls.\n"
            "Produce a structured technical dossier with source references and mechanisms."
        ),
        expected_output=(
            "A structured dossier containing 6-10 validated technical insights, source citations, "
            "algorithmic mechanics, and trade-offs."
        ),
        agent=agent,
    )


def create_analysis_task(agent: Agent, context_tasks: List[Task]) -> Task:
    return Task(
        description=(
            "Analyze the technical dossier from the research phase.\n"
            "1. Query the Neo4j knowledge graph to assess prerequisite concepts.\n"
            "2. Identify new concepts that need to be introduced to the learner.\n"
            "3. Determine the prerequisite dependency order (what must be learned first).\n"
            "4. Register key concepts and relationships in the knowledge graph."
        ),
        expected_output=(
            "A concept topology analysis showing: (a) New concepts, (b) Prerequisite dependencies, "
            "(c) Knowledge gaps, and (d) Recommended teaching order."
        ),
        agent=agent,
        context=context_tasks,
    )


def create_teaching_task(agent: Agent, context_tasks: List[Task]) -> Task:
    return Task(
        description=(
            "Using the research dossier and concept topology, craft an adaptive educational module.\n"
            "1. Explain the topic using intuitive analogies from concepts the student already knows.\n"
            "2. Provide clean code snippets with detached, annotated line-by-line remarks.\n"
            "3. Describe the data flow / architectural diagram in Mermaid.js syntax.\n"
            "4. Highlight critical trade-offs, edge cases, and failure modes."
        ),
        expected_output=(
            "A comprehensive lesson module with intuitive analogies, Mermaid diagram, annotated "
            "code remarks, and key takeaways."
        ),
        agent=agent,
        context=context_tasks,
    )


def create_compose_task(agent: Agent, context_tasks: List[Task]) -> Task:
    return Task(
        description=(
            "Compile all research, concept relationships, and teaching modules into a final lesson guide.\n"
            "Format the guide using standard Markdown sections:\n"
            "# 🚀 Core Architecture & Mental Model\n"
            "## 🧠 Knowledge Graph Connections & Prerequisites\n"
            "## 💻 Code Implementation & Annotations\n"
            "## ⚖️ Trade-offs & Production Realities\n"
            "## 🎯 Actionable Next Steps\n"
        ),
        expected_output=(
            "A publication-ready Markdown lesson document with clear headers, code examples, "
            "prerequisite graph links, and quiz checkpoints."
        ),
        agent=agent,
        context=context_tasks,
    )
