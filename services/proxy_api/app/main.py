from app.api.router import api_router
from fastapi import FastAPI

app = FastAPI(title="Dailymotion API Proxy")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

app.include_router(api_router)
