from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from app.api import api_router
from app.core import settings
from app.services.instance import scheduler_instance
from app.views import frontend_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI app.
    """
    logger.info(f"App started. {settings.PROJECT_NAME}")
    yield
    # Shutdown the scheduler when the app is shutting down
    scheduler_instance.shutdown()
    logger.info(f"App shutting down. {settings.PROJECT_NAME}")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Configure CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Static files and templates
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)

# API ENDPOINTS
app.include_router(api_router, prefix="/api")

# FRONTEND VIEWS
app.include_router(frontend_router)


@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}
