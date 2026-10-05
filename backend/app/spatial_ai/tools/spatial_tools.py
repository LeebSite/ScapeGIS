"""
Controlled Spatial AI Tools

Concrete implementations of spatial tools callable by an AI Agent.
Every tool delegates strictly to verified backend spatial services
and attaches rich provenance metadata.
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.layer_semantic import LayerSemantic
from app.db.models.gis_layer import GISLayer
from app.db.models.gis_dataset import GISDataset
from app.services import spatial_analysis_service as analysis
from app.services import spatial_context_service as context_svc
from app.spatial_ai.tools.base import BaseSpatialTool
from app.spatial_ai.exceptions import SemanticResolutionError, ToolExecutionError
from app.spatial_ai.schemas import (
    FindNearestInput,
    FindNearestOutput,
    NearestFeatureDetails,
    SearchRadiusInput,
    SearchRadiusOutput,
    RadiusFeatureItem,
    GetSpatialContextInput,
    GetSpatialContextOutput,
    CheckContainmentInput,
    CheckContainmentOutput,
    FindIntersectionsInput,
    FindIntersectionsOutput,
    SpatialProvenance,
)


def _extract_feature_name(props: Dict[str, Any]) -> Optional[str]:
    """Helper to extract a friendly feature name from GIS properties."""
    for key in ("NAMOBJ", "REMARK", "name", "nama", "Nama", "LABEL", "KECAMATAN", "DESA"):
        if key in props and props[key]:
            return str(props[key])
    return None


# ── 1. Get Spatial Context Tool ──

class GetSpatialContextTool(BaseSpatialTool):
    name = "get_spatial_context"
    description = (
        "Generate a comprehensive spatial intelligence profile around a coordinate, "
        "including nearest roads (arterial/collector/local), healthcare facilities (hospitals, "
        "clinics), religious buildings, and administrative boundary containment."
    )
    purpose = "Multi-domain spatial context synthesis for developer analysis"
    input_schema = GetSpatialContextInput
    output_schema = GetSpatialContextOutput
    underlying_service = "spatial_context_service.build_spatial_context"

    def execute(
        self,
        db: Session,
        user: User,
        params: Dict[str, Any],
    ) -> GetSpatialContextOutput:
        data: GetSpatialContextInput = self.validate_input(params)
        auth_dataset_ids = self.authorize(db, user, data.workspace_id, data.project_id)

        raw = context_svc.build_spatial_context(
            db=db,
            lat=data.latitude,
            lng=data.longitude,
            workspace_id=data.workspace_id,
            project_id=data.project_id,
        )

        sources: List[SpatialProvenance] = []
        seen_layers = set()

        # Build provenance for facts
        for fact in raw.get("facts", []):
            layer_id = fact.get("layer_id")
            if layer_id and layer_id not in seen_layers:
                seen_layers.add(layer_id)
                layer = db.query(GISLayer).filter(GISLayer.id == UUID(layer_id)).first()
                if layer:
                    dataset = db.query(GISDataset).filter(GISDataset.id == layer.dataset_id).first()
                    sources.append(
                        SpatialProvenance(
                            dataset_id=str(layer.dataset_id),
                            dataset_name=dataset.name if dataset else None,
                            layer_id=str(layer.id),
                            layer_name=layer.name,
                            semantic_category=fact.get("category", "unknown"),
                            semantic_subcategory=fact.get("subcategory", "unknown"),
                            operation=fact.get("type", "spatial_query"),
                        )
                    )

        return GetSpatialContextOutput(
            success=True,
            target={"latitude": data.latitude, "longitude": data.longitude},
            workspace_id=str(data.workspace_id),
            project_id=str(data.project_id) if data.project_id else None,
            project=raw.get("project"),
            authorized_datasets=raw.get("authorized_datasets", []),
            transportation=raw.get("transportation", {}),
            facilities=raw.get("facilities", {}),
            religious=raw.get("religious", {}),
            administrative=raw.get("administrative", {}),
            facts=raw.get("facts", []),
            sources=sources,
            warning=raw.get("warning"),
        )


# ── 2. Find Nearest Tool ──

class FindNearestTool(BaseSpatialTool):
    name = "find_nearest"
    description = (
        "Find the nearest authorized GIS feature for a semantic category (e.g. 'hospital', "
        "'arterial_road', 'mosque', 'police_station') to the target coordinate."
    )
    purpose = "Point-to-feature shortest distance computation via PostGIS"
    input_schema = FindNearestInput
    output_schema = FindNearestOutput
    underlying_service = "spatial_analysis_service.find_nearest_feature"

    def execute(
        self,
        db: Session,
        user: User,
        params: Dict[str, Any],
    ) -> FindNearestOutput:
        data: FindNearestInput = self.validate_input(params)
        auth_dataset_ids = self.authorize(db, user, data.workspace_id, data.project_id)

        # Resolve subcategory dynamically to authorized layers
        layers = analysis.get_layers_for_subcategory(
            db, data.subcategory, authorized_dataset_ids=auth_dataset_ids
        )

        if not layers:
            raise SemanticResolutionError(
                f"No authorized GIS layer found for concept '{data.subcategory}' in this workspace.",
                details={"subcategory": data.subcategory, "workspace_id": str(data.workspace_id)},
            )

        best_result: Optional[Dict[str, Any]] = None
        best_layer: Optional[GISLayer] = None

        for layer in layers:
            res = analysis.find_nearest_feature(db, data.latitude, data.longitude, layer.id)
            if res:
                if (
                    data.max_distance_m is not None
                    and res["distance_meters"] > data.max_distance_m
                ):
                    continue

                if best_result is None or res["distance_meters"] < best_result["distance_meters"]:
                    best_result = res
                    best_layer = layer

        if not best_result or not best_layer:
            return FindNearestOutput(
                success=True,
                category="spatial_analysis",
                subcategory=data.subcategory,
                target={"latitude": data.latitude, "longitude": data.longitude},
                result=None,
                source=None,
                error=f"No feature found for '{data.subcategory}' within distance threshold.",
            )

        # Build provenance
        sem = db.query(LayerSemantic).filter(LayerSemantic.layer_id == best_layer.id).first()
        dataset = db.query(GISDataset).filter(GISDataset.id == best_layer.dataset_id).first()

        provenance = SpatialProvenance(
            dataset_id=str(best_layer.dataset_id),
            dataset_name=dataset.name if dataset else None,
            layer_id=str(best_layer.id),
            layer_name=best_layer.name,
            semantic_category=sem.category if sem else "spatial_analysis",
            semantic_subcategory=data.subcategory,
            operation="ST_DistanceSphere",
            feature_count_queried=1,
        )

        props = best_result.get("properties", {})
        feat_name = _extract_feature_name(props) or (sem.display_name if sem else best_layer.name)

        dist_m = best_result["distance_meters"]

        return FindNearestOutput(
            success=True,
            category=sem.category if sem else "spatial_analysis",
            subcategory=data.subcategory,
            target={"latitude": data.latitude, "longitude": data.longitude},
            result=NearestFeatureDetails(
                feature_id=str(best_result["feature_id"]),
                name=feat_name,
                distance_m=dist_m,
                distance_km=round(dist_m / 1000.0, 3),
                properties=props,
            ),
            source=provenance,
        )


# ── 3. Search Radius Tool ──

class SearchRadiusTool(BaseSpatialTool):
    name = "search_radius"
    description = (
        "Search for all GIS features within a specified radius (in meters) of a target "
        "coordinate for a semantic category (e.g. 'hospital', 'clinic', 'mosque')."
    )
    purpose = "Proximity buffer querying via PostGIS ST_DWithin"
    input_schema = SearchRadiusInput
    output_schema = SearchRadiusOutput
    underlying_service = "spatial_analysis_service.find_features_within_radius"

    def execute(
        self,
        db: Session,
        user: User,
        params: Dict[str, Any],
    ) -> SearchRadiusOutput:
        data: SearchRadiusInput = self.validate_input(params)
        auth_dataset_ids = self.authorize(db, user, data.workspace_id, data.project_id)

        layers = analysis.get_layers_for_subcategory(
            db, data.subcategory, authorized_dataset_ids=auth_dataset_ids
        )

        if not layers:
            raise SemanticResolutionError(
                f"No authorized GIS layer found for concept '{data.subcategory}' in this workspace.",
                details={"subcategory": data.subcategory, "workspace_id": str(data.workspace_id)},
            )

        all_items: List[RadiusFeatureItem] = []
        sources: List[SpatialProvenance] = []

        for layer in layers:
            raw = analysis.find_features_within_radius(
                db=db,
                lat=data.latitude,
                lng=data.longitude,
                layer_id=layer.id,
                radius_meters=data.radius_m,
                limit=data.limit,
            )
            features = raw.get("features", [])
            sem = db.query(LayerSemantic).filter(LayerSemantic.layer_id == layer.id).first()
            dataset = db.query(GISDataset).filter(GISDataset.id == layer.dataset_id).first()

            if features:
                sources.append(
                    SpatialProvenance(
                        dataset_id=str(layer.dataset_id),
                        dataset_name=dataset.name if dataset else None,
                        layer_id=str(layer.id),
                        layer_name=layer.name,
                        semantic_category=sem.category if sem else "spatial_analysis",
                        semantic_subcategory=data.subcategory,
                        operation="ST_DWithin",
                        feature_count_queried=len(features),
                    )
                )

            for f in features:
                props = f.get("properties", {})
                name = _extract_feature_name(props) or (sem.display_name if sem else layer.name)
                dist_m = f["distance_meters"]
                all_items.append(
                    RadiusFeatureItem(
                        feature_id=str(f["feature_id"]),
                        name=name,
                        distance_m=dist_m,
                        distance_km=round(dist_m / 1000.0, 3),
                        properties=props,
                    )
                )

        all_items.sort(key=lambda x: x.distance_m)
        all_items = all_items[:data.limit]

        return SearchRadiusOutput(
            success=True,
            subcategory=data.subcategory,
            target={"latitude": data.latitude, "longitude": data.longitude},
            radius_m=data.radius_m,
            count=len(all_items),
            features=all_items,
            sources=sources,
        )


# ── 4. Check Containment Tool ──

class CheckContainmentTool(BaseSpatialTool):
    name = "check_containment"
    description = (
        "Determine which administrative polygon boundary (e.g. Kecamatan, Kelurahan) "
        "encloses the target coordinate."
    )
    purpose = "Point-in-polygon verification via PostGIS ST_Contains"
    input_schema = CheckContainmentInput
    output_schema = CheckContainmentOutput
    underlying_service = "spatial_analysis_service.find_containing_area"

    def execute(
        self,
        db: Session,
        user: User,
        params: Dict[str, Any],
    ) -> CheckContainmentOutput:
        data: CheckContainmentInput = self.validate_input(params)
        auth_dataset_ids = self.authorize(db, user, data.workspace_id, data.project_id)

        target_layer: Optional[GISLayer] = None

        if data.layer_id:
            target_layer = db.query(GISLayer).filter(GISLayer.id == data.layer_id).first()
            if not target_layer or target_layer.dataset_id not in auth_dataset_ids:
                raise SemanticResolutionError(
                    f"Layer '{data.layer_id}' is not authorized for this workspace.",
                )
        else:
            layers = analysis.get_layers_for_subcategory(
                db, data.subcategory, authorized_dataset_ids=auth_dataset_ids
            )
            if layers:
                target_layer = layers[0]

        if not target_layer:
            raise SemanticResolutionError(
                f"No authorized polygon boundary layer found for concept '{data.subcategory}'.",
                details={"subcategory": data.subcategory},
            )

        containing = analysis.find_containing_area(
            db, data.latitude, data.longitude, target_layer.id
        )

        if not containing:
            return CheckContainmentOutput(
                success=True,
                target={"latitude": data.latitude, "longitude": data.longitude},
                contained=False,
                area_name=None,
                feature_id=None,
                properties={},
                source=None,
            )

        props = containing.get("properties", {})
        area_name = _extract_feature_name(props) or "Administrative Region"

        sem = db.query(LayerSemantic).filter(LayerSemantic.layer_id == target_layer.id).first()
        dataset = db.query(GISDataset).filter(GISDataset.id == target_layer.dataset_id).first()

        provenance = SpatialProvenance(
            dataset_id=str(target_layer.dataset_id),
            dataset_name=dataset.name if dataset else None,
            layer_id=str(target_layer.id),
            layer_name=target_layer.name,
            semantic_category=sem.category if sem else "administrative",
            semantic_subcategory=data.subcategory,
            operation="ST_Contains",
            feature_count_queried=1,
        )

        return CheckContainmentOutput(
            success=True,
            target={"latitude": data.latitude, "longitude": data.longitude},
            contained=True,
            area_name=area_name,
            feature_id=containing.get("feature_id"),
            properties=props,
            source=provenance,
        )


# ── 5. Find Intersections Tool ──

class FindIntersectionsTool(BaseSpatialTool):
    name = "find_intersections"
    description = (
        "Find linear or polygon GIS features (e.g. roads, boundaries) intersecting "
        "a small buffer zone around a target coordinate."
    )
    purpose = "Intersection detection for road access and boundary corridors"
    input_schema = FindIntersectionsInput
    output_schema = FindIntersectionsOutput
    underlying_service = "spatial_analysis_service.find_intersecting_features"

    def execute(
        self,
        db: Session,
        user: User,
        params: Dict[str, Any],
    ) -> FindIntersectionsOutput:
        data: FindIntersectionsInput = self.validate_input(params)
        auth_dataset_ids = self.authorize(db, user, data.workspace_id, data.project_id)

        layers = analysis.get_layers_for_subcategory(
            db, data.subcategory, authorized_dataset_ids=auth_dataset_ids
        )

        if not layers:
            raise SemanticResolutionError(
                f"No authorized GIS layer found for concept '{data.subcategory}' in this workspace.",
            )

        all_features = []
        sources: List[SpatialProvenance] = []

        for layer in layers:
            raw = analysis.find_intersecting_features(
                db=db,
                lat=data.latitude,
                lng=data.longitude,
                layer_id=layer.id,
                buffer_meters=data.buffer_m,
                limit=data.limit,
            )
            features = raw.get("features", [])
            sem = db.query(LayerSemantic).filter(LayerSemantic.layer_id == layer.id).first()
            dataset = db.query(GISDataset).filter(GISDataset.id == layer.dataset_id).first()

            if features:
                sources.append(
                    SpatialProvenance(
                        dataset_id=str(layer.dataset_id),
                        dataset_name=dataset.name if dataset else None,
                        layer_id=str(layer.id),
                        layer_name=layer.name,
                        semantic_category=sem.category if sem else "transportation",
                        semantic_subcategory=data.subcategory,
                        operation="ST_Intersects",
                        feature_count_queried=len(features),
                    )
                )

            for feat in features:
                feat["layer_id"] = str(layer.id)
                feat["layer_name"] = layer.name
                feat["name"] = _extract_feature_name(feat.get("properties", {}))
                all_features.append(feat)

        return FindIntersectionsOutput(
            success=True,
            target={"latitude": data.latitude, "longitude": data.longitude},
            buffer_m=data.buffer_m,
            count=len(all_features),
            features=all_features[:data.limit],
            sources=sources,
        )
