from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cybersec_api.api.routes import router
from cybersec_api.collectors.scheduler import build_scheduler
from cybersec_api.core.config import get_settings
from cybersec_api.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    if settings.collector_scheduler_enabled:
        scheduler = build_scheduler(settings)
        scheduler.start()
        app.state.collector_scheduler = scheduler

    yield

    scheduler = getattr(app.state, "collector_scheduler", None)
    if scheduler is not None:
        scheduler.shutdown(wait=False)


settings = get_settings()

app = FastAPI(
    title="CyberSec API",
    description="Cyber Threat Intelligence Platform API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)
