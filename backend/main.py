from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.websockets.v1.api import api_router
from app.routes.v1.videos import videos_router
from app.core.config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="AI Negotiation Trainer API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(videos_router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok"}
