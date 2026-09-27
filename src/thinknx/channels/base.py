from typing import Protocol, Any, List, Optional


class AbstractChannelAdapter(Protocol):
    """Protocol for channel adapters (Telegram, Slack, Web, etc.)."""

    async def send_message(self, user_id: str, text: str, **kwargs: Any) -> Any:
        """Send plain or markdown formatted message."""
        ...

    async def send_quiz(
        self,
        user_id: str,
        question: str,
        options: List[str],
        callback_prefix: str = "quiz"
    ) -> Any:
        """Send an interactive multiple-choice question with inline actions."""
        ...

    async def send_webapp_button(
        self,
        user_id: str,
        text: str,
        button_label: str,
        url: str
    ) -> Any:
        """Send a message with an embedded Telegram Mini App WebApp button."""
        ...
