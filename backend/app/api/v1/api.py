from fastapi import APIRouter
from app.api.v1.endpoints import auth, admin, gis
from app.api.v1.endpoints.workspaces import router as workspaces_router, invitations_router

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(gis.router)
api_router.include_router(workspaces_router)
api_router.include_router(invitations_router)
