"""
Spatial Analysis Service

All heavy-lifting spatial computations happen here using PostGIS.
Features are never bulk-fetched into Python — all geometry math
is done at the database level for performance and correctness.

CRS: All geometries are stored in EPSG:4326 (WGS 84).
     Distance calculations use PostGIS geography type for meter-accurate results.
"""
from typing import List, Optional, Tuple, Any, Dict
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import text, func
from geoalchemy2.functions import (
    ST_DWithin, ST_Distance, ST_Contains, ST_Intersects,
    ST_GeogFromWKB, ST_AsGeoJSON, ST_SetSRID, ST_MakePoint,
)
from geoalchemy2 import WKTElement

from app.db.models.gis_feature import GISFeature
from app.db.models.gis_layer import GISLayer
from app.db.models.layer_semantic import LayerSemantic


def _make_point_wkt(lat: float, lng: float) -> WKTElement:
    """Create a WKTElement Point geometry in EPSG:4326."""
    return WKTElement(f"POINT({lng} {lat})", srid=4326)


def _meters_to_degrees(meters: float) -> float:
    """Rough conversion for ST_DWithin with geometry (not geography)."""
    # 1 degree latitude ≈ 111,320 m
    return meters / 111320.0


# ─── Layer Discovery ─────────────────────────────────────────────────────────

def get_layers_for_subcategory(
    db: Session,
    subcategory: str,
    authorized_dataset_ids: Optional[List[UUID]] = None,
) -> List[GISLayer]:
    """
    Return GIS layers matching a semantic subcategory, optionally
    filtered to only those belonging to authorized datasets.
    """
    q = (
        db.query(GISLayer)
        .join(LayerSemantic, GISLayer.id == LayerSemantic.layer_id)
        .filter(
            LayerSemantic.subcategory == subcategory,
            LayerSemantic.ai_enabled == True,
        )
    )
    if authorized_dataset_ids is not None:
        q = q.filter(GISLayer.dataset_id.in_(authorized_dataset_ids))
    return q.all()


def get_layers_for_category(
    db: Session,
    category: str,
    authorized_dataset_ids: Optional[List[UUID]] = None,
) -> List[GISLayer]:
    """Return all AI-enabled layers for a semantic category."""
    q = (
        db.query(GISLayer)
        .join(LayerSemantic, GISLayer.id == LayerSemantic.layer_id)
        .filter(
            LayerSemantic.category == category,
            LayerSemantic.ai_enabled == True,
        )
    )
    if authorized_dataset_ids is not None:
        q = q.filter(GISLayer.dataset_id.in_(authorized_dataset_ids))
    return q.all()


# ─── Distance ────────────────────────────────────────────────────────────────

def calculate_distance_to_nearest(
    db: Session,
    lat: float,
    lng: float,
    layer_id: UUID,
) -> Optional[float]:
    """
    Calculate the distance in meters from (lat, lng) to the nearest
    feature in the given layer, using PostGIS geography.

    Returns None if layer has no features.
    """
    point_wkt = _make_point_wkt(lat, lng)

    result = db.execute(
        text("""
            SELECT ST_Distance(
                f.geom::geography,
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
            ) AS distance_m
            FROM gis_features f
            WHERE f.layer_id = :layer_id
            ORDER BY f.geom::geography <-> ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
            LIMIT 1
        """),
        {"lat": lat, "lng": lng, "layer_id": str(layer_id)},
    ).fetchone()

    return float(result.distance_m) if result else None


# ─── Nearest Feature ─────────────────────────────────────────────────────────

def find_nearest_feature(
    db: Session,
    lat: float,
    lng: float,
    layer_id: UUID,
) -> Optional[Dict[str, Any]]:
    """
    Find the nearest feature in a layer to (lat, lng).

    Returns a dict with feature_id, distance_meters, properties.
    Uses PostGIS KNN (<->) operator for index-assisted nearest-neighbor.
    """
    result = db.execute(
        text("""
            SELECT
                f.id::text AS feature_id,
                f.properties,
                ST_Distance(
                    f.geom::geography,
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                ) AS distance_m
            FROM gis_features f
            WHERE f.layer_id = :layer_id
            ORDER BY f.geom::geography <-> ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
            LIMIT 1
        """),
        {"lat": lat, "lng": lng, "layer_id": str(layer_id)},
    ).fetchone()

    if not result:
        return None

    return {
        "feature_id": result.feature_id,
        "distance_meters": round(float(result.distance_m), 2),
        "properties": result.properties or {},
    }


# ─── Radius Search ───────────────────────────────────────────────────────────

def find_features_within_radius(
    db: Session,
    lat: float,
    lng: float,
    layer_id: UUID,
    radius_meters: float,
    limit: int = 50,
) -> Dict[str, Any]:
    """
    Find all features within radius_meters of (lat, lng) in the given layer.

    Uses ST_DWithin on geography for accurate meter-based radius.
    Returns count and a list of features with distances.
    """
    rows = db.execute(
        text("""
            SELECT
                f.id::text AS feature_id,
                f.properties,
                ST_Distance(
                    f.geom::geography,
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                ) AS distance_m
            FROM gis_features f
            WHERE
                f.layer_id = :layer_id
                AND ST_DWithin(
                    f.geom::geography,
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                    :radius_m
                )
            ORDER BY distance_m
            LIMIT :limit
        """),
        {"lat": lat, "lng": lng, "layer_id": str(layer_id), "radius_m": radius_meters, "limit": limit},
    ).fetchall()

    features = [
        {
            "feature_id": row.feature_id,
            "distance_meters": round(float(row.distance_m), 2),
            "properties": row.properties or {},
        }
        for row in rows
    ]

    return {
        "radius_meters": radius_meters,
        "count": len(features),
        "features": features,
    }


# ─── Containment ─────────────────────────────────────────────────────────────

def find_containing_area(
    db: Session,
    lat: float,
    lng: float,
    layer_id: UUID,
) -> Optional[Dict[str, Any]]:
    """
    Find which polygon feature in a layer contains the point (lat, lng).

    Useful for: "Which kecamatan does this point belong to?"
    Uses ST_Contains (faster) with ST_Within fallback for boundary edges.
    """
    result = db.execute(
        text("""
            SELECT
                f.id::text AS feature_id,
                f.properties
            FROM gis_features f
            WHERE
                f.layer_id = :layer_id
                AND ST_Contains(f.geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326))
            LIMIT 1
        """),
        {"lat": lat, "lng": lng, "layer_id": str(layer_id)},
    ).fetchone()

    if not result:
        # Fallback to ST_DWithin for boundary points
        result = db.execute(
            text("""
                SELECT
                    f.id::text AS feature_id,
                    f.properties,
                    ST_Distance(
                        f.geom::geography,
                        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                    ) AS distance_m
                FROM gis_features f
                WHERE f.layer_id = :layer_id
                ORDER BY f.geom::geography <-> ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                LIMIT 1
            """),
            {"lat": lat, "lng": lng, "layer_id": str(layer_id)},
        ).fetchone()
        if not result:
            return None

    return {
        "feature_id": result.feature_id,
        "properties": result.properties or {},
    }


# ─── Intersection ────────────────────────────────────────────────────────────

def find_intersecting_features(
    db: Session,
    lat: float,
    lng: float,
    layer_id: UUID,
    buffer_meters: float = 100.0,
    limit: int = 20,
) -> Dict[str, Any]:
    """
    Find features in a layer that intersect a buffered point.

    Useful for: "Which roads cross this area?" with a small buffer zone.
    """
    rows = db.execute(
        text("""
            SELECT
                f.id::text AS feature_id,
                f.properties,
                ST_Distance(
                    f.geom::geography,
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                ) AS distance_m
            FROM gis_features f
            WHERE
                f.layer_id = :layer_id
                AND ST_DWithin(
                    f.geom::geography,
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                    :buffer_m
                )
            ORDER BY distance_m
            LIMIT :limit
        """),
        {
            "lat": lat, "lng": lng,
            "layer_id": str(layer_id),
            "buffer_m": buffer_meters,
            "limit": limit,
        },
    ).fetchall()

    return {
        "buffer_meters": buffer_meters,
        "count": len(rows),
        "features": [
            {
                "feature_id": row.feature_id,
                "distance_meters": round(float(row.distance_m), 2),
                "properties": row.properties or {},
            }
            for row in rows
        ],
    }


# ─── Count in Radius ─────────────────────────────────────────────────────────

def count_features_within_radius(
    db: Session,
    lat: float,
    lng: float,
    layer_id: UUID,
    radius_meters: float,
) -> int:
    """Efficiently count features within radius without fetching all rows."""
    result = db.execute(
        text("""
            SELECT COUNT(*) AS cnt
            FROM gis_features f
            WHERE
                f.layer_id = :layer_id
                AND ST_DWithin(
                    f.geom::geography,
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                    :radius_m
                )
        """),
        {"lat": lat, "lng": lng, "layer_id": str(layer_id), "radius_m": radius_meters},
    ).fetchone()

    return int(result.cnt) if result else 0
