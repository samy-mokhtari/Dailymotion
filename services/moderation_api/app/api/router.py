from app.api.routes.health import router as health_router
from app.api.routes.videos import router as videos_router
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(videos_router)
