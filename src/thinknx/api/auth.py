from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from thinknx.config import settings
from thinknx.database import get_db
from thinknx.models.user import User
from thinknx.schemas.user import UserResponse, TokenResponse
from thinknx.services.auth_service import (
    create_access_token,
    get_current_user,
    get_default_or_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/dev-token", response_model=TokenResponse, summary="Generate local development token")
async def get_dev_token(db: AsyncSession = Depends(get_db)):
    """Convenience endpoint generating a valid JWT token for local development and testing."""
    if settings.environment != "development":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    user = await get_default_or_current_user(None, db)
    token = create_access_token({"sub": user.id, "email": user.email, "platform": user.platform})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse, summary="Get current user profile")
async def get_me(user: User = Depends(get_current_user)):
    """Returns profile data for the authenticated user."""
    return user
