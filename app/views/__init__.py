from fastapi import APIRouter

from app.views.dashboard import router as dashboard_router
from app.views.index import router as index_router

frontend_router = APIRouter()
frontend_router.include_router(index_router)
frontend_router.include_router(dashboard_router)
