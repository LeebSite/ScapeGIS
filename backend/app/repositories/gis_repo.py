from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from app.db.models.gis_dataset import GISDataset
from app.db.models.gis_layer import GISLayer
from app.db.models.gis_feature import GISFeature
from typing import List, Optional
from uuid import UUID
from geoalchemy2.shape import from_shape
from shapely import wkt


def get_dataset_by_id(db: Session, dataset_id: UUID, user_id: Optional[UUID] = None) -> Optional[GISDataset]:
    """Get a GIS dataset by ID, optionally filtered by user"""
    query = db.query(GISDataset).options(joinedload(GISDataset.layers))
    query = query.filter(GISDataset.id == dataset_id)
    
    if user_id:
        query = query.filter(GISDataset.user_id == user_id)
    
    return query.first()


def get_datasets_by_user(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[GISDataset]:
    """Get all GIS datasets for a user"""
    return db.query(GISDataset)\
        .filter(GISDataset.user_id == user_id)\
        .order_by(desc(GISDataset.created_at))\
        .offset(skip)\
        .limit(limit)\
        .all()


def get_public_datasets(db: Session, skip: int = 0, limit: int = 100) -> List[GISDataset]:
    """Get all public GIS datasets"""
    return db.query(GISDataset)\
        .filter(GISDataset.is_public == True)\
        .filter(GISDataset.status == 'completed')\
        .order_by(desc(GISDataset.created_at))\
        .offset(skip)\
        .limit(limit)\
        .all()


def create_dataset(db: Session, dataset: GISDataset) -> GISDataset:
    """Create a new GIS dataset"""
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def update_dataset(db: Session, dataset_id: UUID, **kwargs) -> Optional[GISDataset]:
    """Update a GIS dataset"""
    dataset = db.query(GISDataset).filter(GISDataset.id == dataset_id).first()
    if dataset:
        for key, value in kwargs.items():
            if value is not None and hasattr(dataset, key):
                setattr(dataset, key, value)
        db.commit()
        db.refresh(dataset)
    return dataset


def delete_dataset(db: Session, dataset_id: UUID) -> bool:
    """Delete a GIS dataset"""
    dataset = db.query(GISDataset).filter(GISDataset.id == dataset_id).first()
    if dataset:
        db.delete(dataset)
        db.commit()
        return True
    return False


# Layer operations
def get_layer_by_id(db: Session, layer_id: UUID) -> Optional[GISLayer]:
    """Get a GIS layer by ID"""
    return db.query(GISLayer).filter(GISLayer.id == layer_id).first()


def get_layers_by_dataset(db: Session, dataset_id: UUID) -> List[GISLayer]:
    """Get all layers for a dataset"""
    return db.query(GISLayer)\
        .filter(GISLayer.dataset_id == dataset_id)\
        .order_by(GISLayer.layer_order)\
        .all()


def create_layer(db: Session, layer: GISLayer) -> GISLayer:
    """Create a new GIS layer"""
    db.add(layer)
    db.commit()
    db.refresh(layer)
    return layer


def update_layer(db: Session, layer_id: UUID, **kwargs) -> Optional[GISLayer]:
    """Update a GIS layer"""
    layer = db.query(GISLayer).filter(GISLayer.id == layer_id).first()
    if layer:
        for key, value in kwargs.items():
            if value is not None and hasattr(layer, key):
                setattr(layer, key, value)
        db.commit()
        db.refresh(layer)
    return layer


def delete_layer(db: Session, layer_id: UUID) -> bool:
    """Delete a GIS layer"""
    layer = db.query(GISLayer).filter(GISLayer.id == layer_id).first()
    if layer:
        db.delete(layer)
        db.commit()
        return True
    return False


def get_dataset_count_by_user(db: Session, user_id: UUID) -> int:
    """Get count of datasets for a user"""
    return db.query(func.count(GISDataset.id))\
        .filter(GISDataset.user_id == user_id)\
        .scalar()


# Feature operations
def create_features_bulk(db: Session, layer_id: UUID, features: List[dict]) -> int:
    """
    Bulk insert features for a layer
    
    Args:
        db: Database session
        layer_id: UUID of the layer
        features: List of dicts with 'geom_wkt' and 'properties'
    
    Returns:
        Number of features created
    """
    feature_objects = []
    
    for feature_data in features:
        try:
            # Parse WKT geometry
            geom_wkt = feature_data['geom_wkt']
            properties = feature_data.get('properties', {})
            
            feature = GISFeature(
                layer_id=layer_id,
                geom=f'SRID=4326;{geom_wkt}',  # PostGIS format
                properties=properties
            )
            feature_objects.append(feature)
        except Exception as e:
            from loguru import logger
            logger.warning(f"Failed to create feature: {str(e)}")
            continue
    
    if feature_objects:
        db.bulk_save_objects(feature_objects)
        db.commit()
    
    return len(feature_objects)


def get_features_by_layer(db: Session, layer_id: UUID, limit: Optional[int] = None) -> List[GISFeature]:
    """
    Get all features for a layer
    
    Args:
        db: Database session
        layer_id: UUID of the layer
        limit: Optional limit on number of features
        
    Returns:
        List of features
    """
    query = db.query(GISFeature).filter(GISFeature.layer_id == layer_id)
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def get_features_as_geojson(db: Session, layer_id: UUID) -> dict:
    """
    Get features as a GeoJSON FeatureCollection
    
    Args:
        db: Database session
        layer_id: UUID of the layer
        
    Returns:
        GeoJSON FeatureCollection dict
    """
    from geoalchemy2.shape import to_shape
    from shapely.geometry import mapping
    
    features = get_features_by_layer(db, layer_id)
    
    geojson_features = []
    for feature in features:
        try:
            # Convert PostGIS geometry to Shapely, then to GeoJSON
            geom = to_shape(feature.geom)
            geojson_feature = {
                "type": "Feature",
                "geometry": mapping(geom),
                "properties": feature.properties or {}
            }
            geojson_features.append(geojson_feature)
        except Exception as e:
            from loguru import logger
            logger.warning(f"Failed to convert feature {feature.id}: {str(e)}")
            continue
    
    return {
        "type": "FeatureCollection",
        "features": geojson_features
    }


def delete_features_by_layer(db: Session, layer_id: UUID) -> bool:
    """Delete all features for a layer"""
    db.query(GISFeature).filter(GISFeature.layer_id == layer_id).delete()
    db.commit()
    return True

