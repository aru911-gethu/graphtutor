from fastapi import APIRouter

from thinknx.api.auth import router as auth_router
from thinknx.api.progress import router as progress_router
from thinknx.api.ws import router as ws_router
from thinknx.api.lesson import router as lesson_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(progress_router)
api_router.include_router(ws_router)
api_router.include_router(lesson_router)
