from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError

from graphtutor.config import settings
from graphtutor.database import get_db
from graphtutor.models.user import User
from graphtutor.services.telegram_auth import validate_telegram_init_data

security = HTTPBearer(auto_error=False)


async def get_current_user_v1(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    x_guest_id: Optional[str] = Header(None, alias="X-Guest-Id"),
    db: AsyncSession = Depends(get_db)
) -> User:
    if x_telegram_init_data and settings.telegram_bot_token:
        is_valid, user_info, _ = validate_telegram_init_data(x_telegram_init_data, settings.telegram_bot_token)
        if is_valid and user_info and "id" in user_info:
            tg_id = str(user_info["id"])
            stmt = select(User).where(User.telegram_id == tg_id)
            res = await db.execute(stmt)
            user = res.scalar_one_or_none()
            if not user:
                user = User(
                    telegram_id=tg_id,
                    name=f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip() or "Telegram User",
                    platform="telegram",
                    explanation_level="intermediate"
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
            return user

    if auth_header and auth_header.credentials:
        token = auth_header.credentials
        user_id = None

        if settings.clerk_secret_key:
            try:
                claims = jwt.decode(
                    token,
                    settings.clerk_secret_key,
                    algorithms=["HS256", "RS256"],
                    options={"verify_aud": False}
                )
                clerk_id = claims.get("sub")
                if clerk_id:
                    stmt = select(User).where(User.clerk_id == clerk_id)
                    res = await db.execute(stmt)
                    user = res.scalar_one_or_none()
                    if not user:
                        email = claims.get("email") or claims.get("sub") + "@clerk.user"
                        name = claims.get("name") or "Learner"
                        user = User(
                            clerk_id=clerk_id,
                            email=email,
                            name=name,
                            platform="web",
                            explanation_level="intermediate"
                        )
                        db.add(user)
                        await db.commit()
                        await db.refresh(user)
                    return user
            except Exception:
                pass

        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
            user_id = payload.get("sub")
        except JWTError:
            pass

        if user_id:
            stmt = select(User).where(User.id == user_id)
            res = await db.execute(stmt)
            user = res.scalar_one_or_none()
            if user:
                return user

    if x_guest_id:
        stmt = select(User).where(User.id == x_guest_id)
        res = await db.execute(stmt)
        guest = res.scalar_one_or_none()
        if guest:
            return guest

    if settings.debug or settings.environment == "development":
        dev_email = "demo@graphtutor.ai"
        stmt = select(User).where(User.email == dev_email)
        res = await db.execute(stmt)
        dev_user = res.scalar_one_or_none()
        if not dev_user:
            dev_user = User(
                email=dev_email,
                name="Demo Explorer",
                platform="web",
                explanation_level="intermediate",
                interests=["Deep Learning", "Mathematics", "DevOps"],
                goals=[{"title": "Master Transformers and Attention", "progress": 0.4}]
            )
            db.add(dev_user)
            await db.commit()
            await db.refresh(dev_user)
        return dev_user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication credentials were missing or invalid.",
        headers={"WWW-Authenticate": "Bearer"}
    )
