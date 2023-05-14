from fastapi import APIRouter
from app.api.v1.endpoints import plugin

api_router = APIRouter()
api_router.include_router(plugin.router, prefix="/plugin", tags=["plugin"])