from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import init_db
from app.core.logging import configure_logging, get_logger
from app.routes import (
    health,
    performance,
    pipeline,
    reviews,
    scenarios,
    subtitles,
    thumbnails,
    topics,
    trends,
    uploads,
)

configure_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    log.info("api.start", model=settings.default_model, channel=settings.channel_name)
    yield
    log.info("api.stop")


app = FastAPI(
    title="Richgo YouTube Automation",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(health.router)
app.include_router(topics.router, prefix="/topics", tags=["topics"])
app.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
app.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
app.include_router(subtitles.router, prefix="/subtitles", tags=["subtitles"])
app.include_router(thumbnails.router, prefix="/thumbnails", tags=["thumbnails"])
app.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
app.include_router(performance.router, prefix="/performance", tags=["performance"])
app.include_router(trends.router, prefix="/trends", tags=["trends"])
app.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"])
