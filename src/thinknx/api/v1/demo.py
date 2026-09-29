import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from thinknx.database import get_db
from thinknx.models.user import User
from thinknx.services.auth_service import create_access_token
from thinknx.schemas.user import UserResponse

router = APIRouter(prefix="/demo", tags=["Demo Guest Session"])


@router.post("/session")
async def create_demo_session(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    guest_uuid = str(uuid.uuid4())
    guest_email = f"guest_{guest_uuid[:8]}@demo.thinknx.ai"

    guest_user = User(
        id=guest_uuid,
        email=guest_email,
        name=f"Guest Learner {guest_uuid[:4].upper()}",
        platform="web_guest",
        explanation_level="intermediate",
        interests=["Deep Learning", "Mathematics", "Cloud Infrastructure"],
        goals=[{"title": "Master Transformers and Attention", "progress": 0.35}]
    )

    db.add(guest_user)
    await db.commit()
    await db.refresh(guest_user)

    token = create_access_token(
        data={"sub": guest_user.id, "guest": True},
        expires_delta=timedelta(days=7)
    )

    return {
        "guest_id": guest_user.id,
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(guest_user),
        "message": "Demo guest session initialized with pre-seeded knowledge graph."
    }
