from app.api.router import api_router
from fastapi import FastAPI

app = FastAPI(title="Moderation API")
app.include_router(api_router)
