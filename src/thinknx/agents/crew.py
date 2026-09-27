from typing import Dict, Any, Optional, Callable
from crewai import Crew, Process

from thinknx.agents.agents import (
    create_researcher_agent,
    create_analyst_agent,
    create_teacher_agent,
    create_composer_agent,
)
from thinknx.agents.tasks import (
    create_research_task,
    create_analysis_task,
    create_teaching_task,
    create_compose_task,
)


class TeachingCrew:
    """Multi-agent CrewAI orchestration for automated deep-dive topic research and curriculum synthesis."""

    def __init__(
        self,
        topic: str,
        depth: str = "working",
        llm: Optional[Any] = None,
        step_callback: Optional[Callable] = None
    ):
        self.topic = topic
        self.depth = depth
        self.llm = llm
        self.step_callback = step_callback

    def build_crew(self) -> Crew:
        researcher = create_researcher_agent(self.llm)
        analyst = create_analyst_agent(self.llm)
        teacher = create_teacher_agent(self.llm)
        composer = create_composer_agent(self.llm)

        t1_research = create_research_task(researcher, self.topic, self.depth)
        t2_analysis = create_analysis_task(analyst, [t1_research])
        t3_teaching = create_teaching_task(teacher, [t1_research, t2_analysis])
        t4_compose = create_compose_task(composer, [t1_research, t2_analysis, t3_teaching])

        return Crew(
            agents=[researcher, analyst, teacher, composer],
            tasks=[t1_research, t2_analysis, t3_teaching, t4_compose],
            process=Process.sequential,
            verbose=True,
            step_callback=self.step_callback,
        )

    def run(self) -> Dict[str, Any]:
        crew = self.build_crew()
        result = crew.kickoff(inputs={"topic": self.topic, "depth": self.depth})
        output_text = str(result.raw if hasattr(result, "raw") else result)

        topics = [self.topic]
        lowered = output_text.lower()
        if "transformer" in lowered:
            topics.append("Transformers")
        if "graph" in lowered or "neo4j" in lowered:
            topics.append("Knowledge Graphs")
        if "attention" in lowered:
            topics.append("Attention Mechanism")

        return {
            "status": "completed",
            "topic": self.topic,
            "content": output_text,
            "topics": list(set(topics)),
        }
