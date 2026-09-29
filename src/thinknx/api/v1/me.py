from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from thinknx.database import get_db
from thinknx.models.user import User
from thinknx.schemas.user import UserResponse, UserUpdateInterests
from thinknx.api.v1.auth_deps import get_current_user_v1

router = APIRouter(prefix="/me", tags=["User Profile"])


@router.get("", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user_v1)):
    return current_user


@router.put("", response_model=UserResponse)
async def update_my_profile(
    update_data: UserUpdateInterests,
    current_user: User = Depends(get_current_user_v1),
    db: AsyncSession = Depends(get_db)
):
    if update_data.interests is not None:
        current_user.interests = update_data.interests
    if update_data.goals is not None:
        current_user.goals = update_data.goals
    if update_data.explanation_level is not None:
        current_user.explanation_level = update_data.explanation_level

    await db.commit()
    await db.refresh(current_user)
    return current_user
