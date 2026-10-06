from fastapi import APIRouter
from app.api.v1.endpoints import auth, admin, gis, projects, spatial, spatial_ai
from app.api.v1.endpoints.workspaces import router as workspaces_router, invitations_router
from app.api.v1.endpoints.gis_access import admin_router as gis_access_admin_router, workspace_gis_router

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(gis.router)
api_router.include_router(workspaces_router)
api_router.include_router(invitations_router)
api_router.include_router(projects.router)
api_router.include_router(gis_access_admin_router)
api_router.include_router(workspace_gis_router)
api_router.include_router(spatial.router)
api_router.include_router(spatial_ai.router)
