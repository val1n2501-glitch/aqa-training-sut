"""Application factory and entry point: python -m app."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import health, tasks, testing
from app.core.config import Settings
from app.core.errors import install_error_handlers
from app.db.database import create_database_engine
from app.db.models import Base

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        engine = create_database_engine(settings.database_url)
        application.state.engine = engine
        try:
            Base.metadata.create_all(engine)
            yield
        finally:
            engine.dispose()

    application = FastAPI(title="Task Manager — Training SUT", version="1.0.0", lifespan=lifespan)
    application.state.settings = settings
    install_error_handlers(application)
    application.include_router(health.router)
    application.include_router(tasks.router)
    if settings.test_mode:
        application.include_router(testing.router)
    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @application.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC_DIR / "index.html")

    return application


app = create_app()
