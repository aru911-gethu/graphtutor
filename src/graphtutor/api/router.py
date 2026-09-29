from fastapi import APIRouter

from graphtutor.api.auth import router as auth_router
from graphtutor.api.progress import router as progress_router
from graphtutor.api.ws import router as ws_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(progress_router)
api_router.include_router(ws_router)
