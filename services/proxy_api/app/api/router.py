from app.api.routes.videos import router as videos_router
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(videos_router)
