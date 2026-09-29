from fastapi import APIRouter

from thinknx.api.v1.me import router as me_router
from thinknx.api.v1.graph import router as graph_router
from thinknx.api.v1.lessons import router as lessons_router
from thinknx.api.v1.reviews import router as reviews_router
from thinknx.api.v1.path import router as path_router
from thinknx.api.v1.ingest import router as ingest_router
from thinknx.api.v1.demo import router as demo_router
from thinknx.api.v1.assessment import router as assessment_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(me_router)
api_v1_router.include_router(graph_router)
api_v1_router.include_router(lessons_router)
api_v1_router.include_router(reviews_router)
api_v1_router.include_router(path_router)
api_v1_router.include_router(ingest_router)
api_v1_router.include_router(demo_router)
api_v1_router.include_router(assessment_router)
