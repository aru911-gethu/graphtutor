from pathlib import Path
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    Centralized, strongly-typed application configuration for thinknx.
    Loads environment variables from .env file or system environment with validation.
    """
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application & Environment
    app_name: str = Field(default="thinknx", description="Application name")
    environment: str = Field(default="development", description="Runtime environment")
    debug: bool = Field(default=True, description="Debug mode flag")
    log_level: str = Field(default="INFO", description="Log level")

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "debug", "dev")
        return bool(v)

    # Auth & Security
    secret_key: str = Field(
        default="dev-secret-key-change-in-production-12345",
        description="JWT and session secret key"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signature algorithm")
    access_token_expire_minutes: int = Field(default=60 * 24, description="Access token expiration in minutes")
    clerk_secret_key: str = Field(default="", description="Clerk Secret Key")
    clerk_issuer: str = Field(default="", description="Clerk JWT Issuer URL")
    base_web_url: str = Field(default="http://localhost:3000", description="Base web app URL")

    # Neo4j Database
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j Bolt connection URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="changeme", description="Neo4j password")

    # Relational Database & Task Queue
    database_url: str = Field(
        default="sqlite+aiosqlite:///./thinknx.db",
        description="SQLAlchemy async connection URL"
    )
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis broker and cache URL")

    # Telegram Bot
    telegram_bot_token: str = Field(default="", description="Telegram Bot API Token")

    # LLM APIs
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    openai_api_key: str = Field(default="", description="OpenAI API key")

    # Hostinger KV2
    kv2_endpoint: str = Field(default="", description="Hostinger KV2 REST endpoint")
    kv2_token: str = Field(default="", description="Hostinger KV2 Auth token")

    # Model Routing
    model_extract: str = Field(default="claude-haiku-4-5-20251001", description="Model for concept extraction")
    model_teach: str = Field(default="claude-sonnet-5-20250514", description="Model for adaptive teaching")
    model_complex: str = Field(default="claude-opus-5-5-20250918", description="Model for complex synthesis")
    model_vision: str = Field(default="claude-sonnet-5-20250514", description="Model for vision processing")

    data_dir: Path = Field(default=ROOT_DIR / "data", description="Data directory")
    graph_dir: Path = Field(default=ROOT_DIR / "data" / "graph", description="Graph snapshots and HTML exports")
    cache_dir: Path = Field(default=ROOT_DIR / "data" / "cache", description="Cache directory")

    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed frontend CORS origins"
    )

    def ensure_runtime_dirs(self):
        for d in [self.data_dir, self.graph_dir, self.cache_dir]:
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
