"""
GIS Service - Handles GIS dataset and layer operations
Implements full ZIP processing workflow as specified
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status, UploadFile
from app.repositories import gis_repo
from app.db.models.gis_dataset import GISDataset
from app.db.models.gis_layer import GISLayer
from app.schemas.gis_schema import (
    GISDatasetCreateRequest,
    GISDatasetUpdateRequest,
    GISDatasetResponse,
    GISDatasetListResponse,
    GISLayerCreateRequest,
    GISLayerUpdateRequest,
    GISLayerResponse
)
from app.core.gis_processor import GISProcessor
import json
import os
import tempfile
import shutil
from pathlib import Path
from loguru import logger


# Initialize GIS processor
gis_processor = GISProcessor()


def get_user_datasets(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[GISDatasetListResponse]:
    """Get all datasets for a user with summary info"""
    datasets = gis_repo.get_datasets_by_user(db, user_id, skip, limit)
    
    results = []
    for dataset in datasets:
        results.append(GISDatasetListResponse(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            file_type=dataset.file_type,
            status=dataset.status,
            is_public=dataset.is_public,
            layer_count=len(dataset.layers) if dataset.layers else 0,
            created_at=dataset.created_at
        ))
    
    return results


def get_dataset_detail(db: Session, dataset_id: UUID, user_id: Optional[UUID] = None) -> GISDatasetResponse:
    """Get detailed dataset information"""
    dataset = gis_repo.get_dataset_by_id(db, dataset_id, user_id)
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    return GISDatasetResponse.model_validate(dataset)


def _merge_bboxes(bboxes: List[List[float]]) -> List[float]:
    """
    Merge multiple bounding boxes into one
    
    Args:
        bboxes: List of bboxes [minx, miny, maxx, maxy]
        
    Returns:
        Merged bbox [minx, miny, max maxy]
    """
    if not bboxes:
        return None
    
    minx = min(bbox[0] for bbox in bboxes)
    miny = min(bbox[1] for bbox in bboxes)
    maxx = max(bbox[2] for bbox in bboxes)
    maxy = max(bbox[3] for bbox in bboxes)
    
    return [minx, miny, maxx, maxy]


async def upload_and_process_dataset(
    db: Session,
    user_id: UUID,
    name: str,
    file: UploadFile,
    description: Optional[str] = None,
    is_public: bool = False
) -> GISDatasetResponse:
    """
    🟢 MAIN WORKFLOW: Upload ZIP and process GIS data
    
    Flow:
    1. Admin upload ZIP
    2. Backend save ZIP temporarily
    3. Extract ZIP
    4. Identify GIS files
    5. Convert to GeoJSON (if needed)
    6. Transform CRS to EPSG:4326
    7. Insert data to PostGIS
    8. Expose API for frontend
    """
    temp_file_path = None
    
    try:
        # ========================================
        # STEP 1: Save ZIP file temporarily
        # ========================================
        logger.info(f"Processing upload: {file.filename}")
        
        # Validate file is ZIP
        if not file.filename.endswith('.zip'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only ZIP files are accepted"
            )
        
        # Save uploaded file to temp location
        temp_file_path = tempfile.mktemp(suffix='.zip')
        
        with open(temp_file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        file_size = os.path.getsize(temp_file_path)
        logger.info(f"Saved ZIP file: {temp_file_path} ({file_size} bytes)")
        
        # ========================================
        # STEP 2-6: Extract and process ZIP
        # ========================================
        dataset = GISDataset(
            user_id=user_id,
            name=name,
            description=description,
            original_filename=file.filename,
            file_type='pending',  # Will be updated after processing
            file_size=file_size,
            is_public=is_public,
            status='processing'
        )
        
        dataset = gis_repo.create_dataset(db, dataset)
        logger.info(f"Created dataset: {dataset.id}")
        
        try:
            # Process the ZIP file - now returns LIST of (file_type, layer_name, gdf)
            layers_data = gis_processor.process_zip_upload(temp_file_path)
            
            if not layers_data:
                raise ValueError("No valid GIS files found in ZIP")
            
            logger.info(f"Found {len(layers_data)} layers to process")
            
            # Calculate dataset-level statistics
            total_features = 0
            all_geometry_types = set()
            all_bounds = []
            
            # Process each layer
            created_layers = []
            for file_type, layer_name, gdf in layers_data:
                try:
                    # Extract features and metadata for this layer
                    features_data, metadata = gis_processor.extract_features(gdf)
                    
                    total_features += metadata['total_features']
                    all_geometry_types.update(metadata['geometry_types'])
                    if metadata.get('bbox'):
                        all_bounds.append(metadata['bbox'])
                    
                    # Create GeoJSON preview
                    geojson_preview = gis_processor.create_geojson_preview(gdf, max_features=1000)
                    
                    # Create layer
                    layer = GISLayer(
                        dataset_id=dataset.id,
                        name=layer_name,
                        description=f"Layer {layer_name} from {file.filename}",
                        geometry_type=metadata['primary_geometry_type'],
                        feature_count=metadata['total_features'],
                        bbox=metadata.get('bbox'),
                        crs=metadata['crs'],
                        geojson_data=geojson_preview,
                        properties_schema=metadata.get('properties_schema'),
                        layer_order=len(created_layers)
                    )
                    
                    layer = gis_repo.create_layer(db, layer)
                    logger.info(f"Created layer: {layer.name} ({layer.feature_count} features)")
                    
                    # Insert features to PostGIS
                    feature_count = gis_repo.create_features_bulk(db, layer.id, features_data)
                    
                    # Update layer feature count
                    layer.feature_count = feature_count
                    db.commit()
                    
                    created_layers.append(layer)
                    logger.info(f"✅ Inserted {feature_count} features for layer {layer.name}")
                    
                except Exception as e:
                    logger.warning(f"Failed to process layer {layer_name}: {str(e)}")
                    continue
            
            if not created_layers:
                raise ValueError("Failed to process any layers from ZIP")
            
            # Update dataset with aggregate metadata
            dataset.file_type = layers_data[0][0]  # Use first file type
            dataset.crs = 'EPSG:4326'
            dataset.bbox = _merge_bboxes(all_bounds) if all_bounds else None
            
            # Populate dataset fields
            dataset.source = "upload"
            dataset.srid = 4326
            dataset.total_layers = len(created_layers)
            dataset.total_features = total_features
            dataset.geometry_type = list(all_geometry_types)[0] if all_geometry_types else 'Mixed'
            dataset.status = 'completed'
            
            db.commit()
            logger.info(f"✅ Dataset complete: {len(created_layers)} layers, {total_features} total features")
            
        except Exception as e:
            # Update dataset status to failed
            dataset.status = 'failed'
            dataset.error_message = str(e)
            db.commit()
            
            logger.error(f"Processing failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process GIS file: {str(e)}"
            )
        
        # Refresh dataset with layers relationship
        db.refresh(dataset)
        # Explicitly load layers relationship
        dataset = gis_repo.get_dataset_by_id(db, dataset.id)
        
        return GISDatasetResponse.model_validate(dataset)
        
    finally:
        # Cleanup temp file
        if temp_file_path:
            gis_processor.cleanup_temp_file(temp_file_path)


def create_dataset(
    db: Session,
    user_id: UUID,
    payload: GISDatasetCreateRequest,
    file: Optional[UploadFile] = None
) -> GISDatasetResponse:
    """Create a new GIS dataset (deprecated - use upload_and_process_dataset)"""
    
    # Determine file type from upload
    file_type = "unknown"
    original_filename = "manual_upload"
    file_size = 0
    
    if file:
        original_filename = file.filename
        # Determine file type from extension
        ext = Path(original_filename).suffix.lower()
        if ext == '.geojson' or ext == '.json':
            file_type = 'geojson'
        elif ext == '.kml':
            file_type = 'kml'
        elif ext == '.shp':
            file_type = 'shapefile'
        elif ext == '.gpkg':
            file_type = 'geopackage'
    
    # Create dataset
    dataset = GISDataset(
        user_id=user_id,
        name=payload.name,
        description=payload.description,
        original_filename=original_filename,
        file_type=file_type,
        file_size=file_size,
        is_public=payload.is_public,
        status='pending'
    )
    
    dataset = gis_repo.create_dataset(db, dataset)
    
    # TODO: Process file in background task
    # For now, we'll set status to completed
    dataset.status = 'completed'
    db.commit()
    db.refresh(dataset)
    
    return GISDatasetResponse.model_validate(dataset)


def update_dataset(
    db: Session,
    dataset_id: UUID,
    user_id: UUID,
    payload: GISDatasetUpdateRequest
) -> GISDatasetResponse:
    """Update a dataset"""
    
    # Check ownership
    dataset = gis_repo.get_dataset_by_id(db, dataset_id, user_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )
    
    # Update fields
    update_data = payload.model_dump(exclude_unset=True)
    dataset = gis_repo.update_dataset(db, dataset_id, **update_data)
    
    return GISDatasetResponse.model_validate(dataset)


def delete_dataset(db: Session, dataset_id: UUID, user_id: UUID) -> dict:
    """Delete a dataset"""
    
    # Check ownership
    dataset = gis_repo.get_dataset_by_id(db, dataset_id, user_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )
    
    success = gis_repo.delete_dataset(db, dataset_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete dataset"
        )
    
    return {"message": "Dataset deleted successfully"}


# Layer operations
def get_dataset_layers(db: Session, dataset_id: UUID) -> List[GISLayerResponse]:
    """Get all layers for a dataset"""
    layers = gis_repo.get_layers_by_dataset(db, dataset_id)
    return [GISLayerResponse.model_validate(layer) for layer in layers]


def get_layer_geojson(db: Session, layer_id: UUID) -> dict:
    """
    🟢 API: Get layer as GeoJSON for frontend map preview
    
    Returns:
        GeoJSON FeatureCollection in EPSG:4326
    """
    # Check if layer exists
    layer = gis_repo.get_layer_by_id(db, layer_id)
    if not layer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Layer not found"
        )
    
    # Get features as GeoJSON from PostGIS
    geojson = gis_repo.get_features_as_geojson(db, layer_id)
    
    return geojson


def create_layer(
    db: Session,
    dataset_id: UUID,
    user_id: UUID,
    payload: GISLayerCreateRequest
) -> GISLayerResponse:
    """Create a new layer in a dataset"""
    
    # Check dataset ownership
    dataset = gis_repo.get_dataset_by_id(db, dataset_id, user_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or access denied"
        )
    
    # Create layer
    layer = GISLayer(
        dataset_id=dataset_id,
        name=payload.name,
        description=payload.description,
        geometry_type=payload.geometry_type,
        geojson_data=payload.geojson_data,
        style=payload.style
    )
    
    layer = gis_repo.create_layer(db, layer)
    
    return GISLayerResponse.model_validate(layer)


def update_layer(
    db: Session,
    layer_id: UUID,
    user_id: UUID,
    payload: GISLayerUpdateRequest
) -> GISLayerResponse:
    """Update a layer"""
    
    # Get layer and check ownership
    layer = gis_repo.get_layer_by_id(db, layer_id)
    if not layer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Layer not found"
        )
    
    dataset = gis_repo.get_dataset_by_id(db, layer.dataset_id, user_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update fields
    update_data = payload.model_dump(exclude_unset=True)
    layer = gis_repo.update_layer(db, layer_id, **update_data)
    
    return GISLayerResponse.model_validate(layer)


def delete_layer(db: Session, layer_id: UUID, user_id: UUID) -> dict:
    """Delete a layer"""
    
    # Get layer and check ownership
    layer = gis_repo.get_layer_by_id(db, layer_id)
    if not layer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Layer not found"
        )
    
    dataset = gis_repo.get_dataset_by_id(db, layer.dataset_id, user_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    success = gis_repo.delete_layer(db, layer_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete layer"
        )
    
    return {"message": "Layer deleted successfully"}
