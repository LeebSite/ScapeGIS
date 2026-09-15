from fastapi import APIRouter
from app.api.v1.endpoints import auth, admin, gis

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(gis.router)


