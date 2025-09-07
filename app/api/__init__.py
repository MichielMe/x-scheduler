from fastapi import APIRouter

from app.api.endpoints import scheduler, uploads

api_router = APIRouter()
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
