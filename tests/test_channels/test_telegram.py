import pytest
from unittest.mock import AsyncMock, MagicMock
from graphtutor.channels.telegram import TelegramBot
from graphtutor.learning.engine import slugify


def test_slugify():
    """Verify topic slugification."""
    assert slugify("Attention Mechanism") == "attention-mechanism"
    assert slugify("Docker & Containers!") == "docker-containers"
    assert slugify("Large Language Models") == "large-language-models"


def test_telegram_bot_initialization(mock_neo4j_driver):
    """Verify TelegramBot can initialize handlers without error."""
    bot = TelegramBot(token=None, base_web_url="http://localhost:8000")
    assert bot.app is None  # no token provided, gracefully handles offline

    # Test with dummy token
    bot_with_token = TelegramBot(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11", base_web_url="http://localhost:8000")
    assert bot_with_token.app is not None
