import asyncio
from typing import Any
from thinknx.api.ws import broadcast_agent_step


class AgentStepBroadcaster:
    """Dispatches live CrewAI agent execution steps to connected WebSocket sessions."""

    def __init__(self, task_id: str):
        self.task_id = task_id

    def __call__(self, step_output: Any):
        try:
            agent_name = getattr(step_output, "agent", "Teaching Crew Agent")
            thought = str(getattr(step_output, "thought", getattr(step_output, "output", "")))

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(broadcast_agent_step(self.task_id, str(agent_name), thought[:250]))
            except Exception:
                pass
        except Exception:
            pass
