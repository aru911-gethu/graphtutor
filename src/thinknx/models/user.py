import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.orm import relationship

from thinknx.database import Base


class User(Base):
    """Registered user profile with preferences, learning goals, and channel metadata."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=True)
    clerk_id = Column(String(255), unique=True, index=True, nullable=True)
    telegram_id = Column(String(100), unique=True, index=True, nullable=True)
    name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    platform = Column(String(50), default="telegram", index=True)
    explanation_level = Column(String(50), default="beginner")  # beginner, intermediate, advanced
    timezone = Column(String(50), default="UTC")
    interests = Column(JSON, default=list)  # List of interest topic strings
    goals = Column(JSON, default=list)      # List of target goals / concepts
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    sessions = relationship("LearningSession", back_populates="user", cascade="all, delete-orphan")
