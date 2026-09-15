"""
GIS API Endpoints
Provides RESTful API for GIS dataset and layer management
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Query, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.services import gis_service
from app.schemas.gis_schema import (
    GISDatasetCreateRequest,
    GISDatasetUpdateRequest,
    GISDatasetResponse,
    GISDatasetListResponse,
    GISLayerCreateRequest,
    GISLayerUpdateRequest,
    GISLayerResponse
)

router = APIRouter(prefix="/gis", tags=["GIS"])


# ==========================================================================
# 🟢 DATASET ENDPOINTS
# ==========================================================================

@router.get("/datasets", response_model=List[GISDatasetListResponse])
def get_user_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all GIS datasets for the current user
    """
    return gis_service.get_user_datasets(db, current_user.id, skip, limit)


@router.get("/datasets/{dataset_id}", response_model=GISDatasetResponse)
def get_dataset_detail(
    dataset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    📊 API: Get dataset metadata
    
    Response includes:
    - name, geometry_type, total_layers, total_features
    - srid (always 4326 for frontend)
    - bbox, status, etc.
    """
    return gis_service.get_dataset_detail(db, dataset_id, current_user.id)


@router.post("/datasets", response_model=GISDatasetResponse)
def create_dataset(
    payload: GISDatasetCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new GIS dataset (manual creation)
    """
    return gis_service.create_dataset(db, current_user.id, payload)


@router.post("/upload", response_model=GISDatasetResponse)
async def upload_gis_zip(
    file: UploadFile = File(..., description="ZIP file containing GIS data"),
    name: str = Form(..., description="Dataset name"),
    description: Optional[str] = Form(None, description="Dataset description"),
    is_public: bool = Form(False, description="Make dataset public"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🟢 MAIN ENDPOINT: Upload ZIP containing GIS data
    
    Workflow:
    1. Accept ZIP file upload
    2. Extract and identify GIS files (.geojson, .shp, etc.)
    3. Parse and convert to GeoDataFrame
    4. Transform CRS to EPSG:4326
    5. Insert features to PostGIS (gis_features table)
    6. Create dataset and layer records
    7. Return dataset info
    
    Supported formats in ZIP:
    - GeoJSON (.geojson, .json)
    - Shapefile (.shp + .shx, .dbf, .prj)
    - KML (.kml)
    - GeoPackage (.gpkg)
    - QGIS Metadata (.qmd) - optional, for metadata only
    
    Returns:
    - Dataset with status: 'completed' or 'failed'
    - Layers with feature_count
    - All geometries stored in EPSG:4326
    """
    return await gis_service.upload_and_process_dataset(
        db=db,
        user_id=current_user.id,
        name=name,
        file=file,
        description=description,
        is_public=is_public
    )


@router.put("/datasets/{dataset_id}", response_model=GISDatasetResponse)
def update_dataset(
    dataset_id: UUID,
    payload: GISDatasetUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a dataset
    """
    return gis_service.update_dataset(db, dataset_id, current_user.id, payload)


@router.delete("/datasets/{dataset_id}")
def delete_dataset(
    dataset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a dataset and all its layers/features
    """
    return gis_service.delete_dataset(db, dataset_id, current_user.id)


# ==========================================================================
# 🟢 LAYER ENDPOINTS
# ==========================================================================

@router.get("/datasets/{dataset_id}/layers", response_model=List[GISLayerResponse])
def get_dataset_layers(
    dataset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all layers for a dataset
    """
    return gis_service.get_dataset_layers(db, dataset_id)


@router.get("/layers/{layer_id}/geojson")
def get_layer_geojson(
    layer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🟢 API: Preview Map (GeoJSON)
    
    Get layer data as GeoJSON FeatureCollection for Leaflet preview
    
    Response format:
    {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": { ... },
          "properties": { ... }
        }
      ]
    }
    
    All geometries are in EPSG:4326 (WGS 84)
    """
    return gis_service.get_layer_geojson(db, layer_id)


@router.post("/datasets/{dataset_id}/layers", response_model=GISLayerResponse)
def create_layer(
    dataset_id: UUID,
    payload: GISLayerCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new layer in a dataset
    """
    return gis_service.create_layer(db, dataset_id, current_user.id, payload)


@router.put("/layers/{layer_id}", response_model=GISLayerResponse)
def update_layer(
    layer_id: UUID,
    payload: GISLayerUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a layer
    """
    return gis_service.update_layer(db, layer_id, current_user.id, payload)


@router.delete("/layers/{layer_id}")
def delete_layer(
    layer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a layer and all its features
    """
    return gis_service.delete_layer(db, layer_id, current_user.id)
