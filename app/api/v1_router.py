from fastapi import APIRouter

from app.api.routes.v1 import health, items

v1_router = APIRouter()
v1_router.include_router(health.router, prefix="/health")
v1_router.include_router(items.router)
