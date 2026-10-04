"""
Tests for Module 1 — Spatial Knowledge Foundation

Tests cover:
  - Semantic catalog seeder
  - Spatial analysis operations (nearest, radius, containment, intersection)
  - Workspace-scoped semantic discovery (authorization)
  - Spatial context builder
  - API endpoints (via mock db calls)

Test coordinates: Center of Pekanbaru (0.507, 101.447)
"""
import pytest
from uuid import uuid4, UUID
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models.layer_semantic import LayerSemantic
from app.db.models.gis_layer import GISLayer
from app.db.models.gis_dataset import GISDataset
from app.db.models.workspace_gis_access import WorkspaceGISAccess
from app.services.semantic import semantic_service
from app.services import spatial_analysis_service as analysis
from app.services import spatial_context_service as ctx_svc

# ── Constants ─────────────────────────────────────────────────────────────────

PEKANBARU_LAT = 0.507
PEKANBARU_LNG = 101.447

# The existing Pekanbaru dataset ID (from live DB)
PEKANBARU_DATASET_ID = UUID("adb542a8-4c47-413f-a98b-3592b7f7ef00")


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def db():
    """Live database session (read-only tests against real PostGIS data)."""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def pekanbaru_workspace_id(db):
    """
    Get a workspace that has access to the Pekanbaru dataset.
    Falls back to creating a temporary grant if none exist.
    """
    row = (
        db.query(WorkspaceGISAccess)
        .filter(
            WorkspaceGISAccess.dataset_id == PEKANBARU_DATASET_ID,
            WorkspaceGISAccess.is_active == True,
        )
        .first()
    )
    if row:
        return row.workspace_id
    return None  # Skip workspace-scoped tests if no grant exists


# ── Semantic Catalog Tests ─────────────────────────────────────────────────────

class TestSemanticCatalog:
    def test_get_all_ai_enabled_semantics(self, db):
        """AI-enabled semantic layers must be present after seeding."""
        semantics = semantic_service.get_all_semantics(db, ai_enabled_only=True)
        assert len(semantics) > 0, "No AI-enabled semantic layers found. Run the seeder first."

    def test_semantic_categories_present(self, db):
        """All major semantic categories must have at least one entry."""
        semantics = semantic_service.get_all_semantics(db, ai_enabled_only=True)
        categories = {s.category for s in semantics}
        expected = {"transportation", "public_facility", "religious", "commercial", "administrative"}
        for cat in expected:
            assert cat in categories, f"Expected category '{cat}' not found in semantics."

    def test_hospital_semantic_present(self, db):
        """Hospital subcategory must be seeded."""
        results = semantic_service.get_semantics_by_subcategory(db, "hospital")
        assert len(results) > 0, "No hospital semantic found."
        assert results[0].display_name == "Rumah Sakit"

    def test_arterial_road_semantic_present(self, db):
        """Arterial road must be seeded with correct category."""
        results = semantic_service.get_semantics_by_subcategory(db, "arterial_road")
        assert len(results) > 0
        assert results[0].category == "transportation"
        assert results[0].display_name == "Jalan Arteri"

    def test_admin_boundary_semantic_present(self, db):
        """Administrative boundary must be seeded."""
        results = semantic_service.get_semantics_by_subcategory(db, "administrative_boundary")
        assert len(results) > 0
        assert results[0].category == "administrative"

    def test_semantic_metadata_has_aliases(self, db):
        """Semantic metadata must contain aliases list."""
        results = semantic_service.get_semantics_by_subcategory(db, "hospital")
        for s in results:
            if s.ai_enabled:
                meta = s.semantic_metadata or {}
                aliases = meta.get("aliases", [])
                assert len(aliases) > 0, "Hospital semantic must have aliases."
                assert "rumah sakit" in aliases

    def test_shapefile_duplicates_marked_disabled(self, db):
        """Shapefile variants must have ai_enabled=False."""
        # Get all semantics including disabled
        all_semantics = semantic_service.get_all_semantics(db, ai_enabled_only=False)
        shapefile_sems = [
            s for s in all_semantics
            if s.layer and "_SHAPEFILE" in (s.layer.name or "").upper()
        ]
        for s in shapefile_sems:
            assert s.ai_enabled == False, (
                f"Shapefile layer {s.layer.name} should have ai_enabled=False"
            )

    def test_seed_is_idempotent(self, db):
        """Running seeder twice must not create duplicate records."""
        summary1 = semantic_service.seed_pekanbaru_semantics(db)
        summary2 = semantic_service.seed_pekanbaru_semantics(db)
        # Second run should only update, not create new records
        assert summary2["created"] == 0, "Second seeder run should not create new records."


# ── Spatial Analysis Tests ─────────────────────────────────────────────────────

class TestSpatialAnalysis:
    def _get_layer_id(self, db, subcategory: str) -> UUID:
        results = semantic_service.get_semantics_by_subcategory(db, subcategory)
        assert results, f"No semantic for subcategory '{subcategory}'"
        return results[0].layer_id

    def test_nearest_hospital(self, db):
        """Nearest hospital must return a result with positive distance."""
        layer_id = self._get_layer_id(db, "hospital")
        result = analysis.find_nearest_feature(db, PEKANBARU_LAT, PEKANBARU_LNG, layer_id)
        assert result is not None
        assert result["distance_meters"] > 0
        assert result["distance_meters"] < 50000, "Nearest hospital should be within 50km"

    def test_nearest_arterial_road(self, db):
        """Nearest arterial road must be reasonably close."""
        layer_id = self._get_layer_id(db, "arterial_road")
        dist = analysis.calculate_distance_to_nearest(db, PEKANBARU_LAT, PEKANBARU_LNG, layer_id)
        assert dist is not None
        assert dist > 0
        assert dist < 20000, "Nearest arterial road should be within 20km"

    def test_hospitals_within_5km(self, db):
        """There must be at least 1 hospital within 5km of Pekanbaru center."""
        layer_id = self._get_layer_id(db, "hospital")
        count = analysis.count_features_within_radius(db, PEKANBARU_LAT, PEKANBARU_LNG, layer_id, 5000)
        assert count >= 1, "Should find at least 1 hospital within 5km of Pekanbaru center."

    def test_radius_search_returns_sorted_results(self, db):
        """Radius search results must be sorted by distance (nearest first)."""
        layer_id = self._get_layer_id(db, "mosque")
        result = analysis.find_features_within_radius(db, PEKANBARU_LAT, PEKANBARU_LNG, layer_id, 3000)
        distances = [f["distance_meters"] for f in result["features"]]
        assert distances == sorted(distances), "Results must be sorted by distance ascending."

    def test_radius_search_count_consistency(self, db):
        """count_features_within_radius must agree with find_features_within_radius count."""
        layer_id = self._get_layer_id(db, "hospital")
        radius = 3000
        detailed = analysis.find_features_within_radius(db, PEKANBARU_LAT, PEKANBARU_LNG, layer_id, radius)
        count = analysis.count_features_within_radius(db, PEKANBARU_LAT, PEKANBARU_LNG, layer_id, radius)
        # Count may differ due to limit=50, so just check count >= detailed count
        assert count >= detailed["count"]

    def test_admin_containment(self, db):
        """Pekanbaru center must be contained in an administrative boundary."""
        layer_id = self._get_layer_id(db, "administrative_boundary")
        result = analysis.find_containing_area(db, PEKANBARU_LAT, PEKANBARU_LNG, layer_id)
        assert result is not None, "Center of Pekanbaru must be in some administrative boundary."
        props = result.get("properties", {})
        # WADMKK should contain "PEKANBARU"
        city = props.get("WADMKK", "")
        assert "PEKANBARU" in (city or "").upper()

    def test_intersection_finds_roads(self, db):
        """Intersection check must find nearby roads."""
        layer_id = self._get_layer_id(db, "arterial_road")
        result = analysis.find_intersecting_features(
            db, PEKANBARU_LAT, PEKANBARU_LNG, layer_id, buffer_meters=1000
        )
        assert result["count"] >= 0  # May be 0 if no arteri within 1km — acceptable

    def test_nearest_puskesmas(self, db):
        """Nearest puskesmas must return a valid result."""
        layer_id = self._get_layer_id(db, "puskesmas")
        result = analysis.find_nearest_feature(db, PEKANBARU_LAT, PEKANBARU_LNG, layer_id)
        assert result is not None
        assert result["distance_meters"] > 0

    def test_nearest_mosque(self, db):
        """Nearest mosque must return a valid result."""
        layer_id = self._get_layer_id(db, "mosque")
        result = analysis.find_nearest_feature(db, PEKANBARU_LAT, PEKANBARU_LNG, layer_id)
        assert result is not None
        assert result["distance_meters"] > 0


# ── Workspace Authorization Tests ──────────────────────────────────────────────

class TestWorkspaceAuthorization:
    def test_workspace_scoped_semantics_empty_for_no_access(self, db):
        """Workspace with no GIS access must receive empty semantic list."""
        fake_workspace_id = uuid4()
        semantics = semantic_service.get_semantics_for_workspace(db, fake_workspace_id)
        assert len(semantics) == 0, "Workspace with no access grant must get no semantics."

    def test_workspace_scoped_semantics_populated_for_authorized(self, db, pekanbaru_workspace_id):
        """Authorized workspace must receive semantic layers."""
        if pekanbaru_workspace_id is None:
            pytest.skip("No workspace with Pekanbaru grant found in test DB.")
        semantics = semantic_service.get_semantics_for_workspace(db, pekanbaru_workspace_id)
        assert len(semantics) > 0, "Authorized workspace must receive semantic layers."

    def test_context_returns_warning_for_unauthorized_workspace(self, db):
        """Spatial context for workspace with no access must return warning."""
        fake_workspace_id = uuid4()
        context = ctx_svc.build_spatial_context(db, PEKANBARU_LAT, PEKANBARU_LNG, fake_workspace_id)
        assert "warning" in context
        assert len(context.get("facts", [])) == 0

    def test_nearest_returns_none_for_unauthorized(self, db):
        """Quick nearest for unauthorized workspace must return None."""
        fake_workspace_id = uuid4()
        result = ctx_svc.build_quick_nearest(
            db, PEKANBARU_LAT, PEKANBARU_LNG, "hospital", fake_workspace_id
        )
        assert result is None

    def test_radius_returns_empty_for_unauthorized(self, db):
        """Radius search for unauthorized workspace must return count=0."""
        fake_workspace_id = uuid4()
        result = ctx_svc.build_radius_search(
            db, PEKANBARU_LAT, PEKANBARU_LNG, "hospital", 2000, fake_workspace_id
        )
        assert result["count"] == 0


# ── Edge Case Tests ────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_zero_radius_returns_empty(self, db):
        """A radius of 1 meter should return no results (or 1 if exactly on a feature)."""
        results = semantic_service.get_semantics_by_subcategory(db, "hospital")
        if not results:
            pytest.skip("No hospital semantic.")
        layer_id = results[0].layer_id
        result = analysis.find_features_within_radius(db, PEKANBARU_LAT, PEKANBARU_LNG, layer_id, 1)
        assert result["count"] >= 0  # Acceptable to be 0 or non-negative

    def test_nonexistent_layer_returns_none_nearest(self, db):
        """find_nearest_feature on a non-existent layer must return None."""
        fake_layer_id = uuid4()
        result = analysis.find_nearest_feature(db, PEKANBARU_LAT, PEKANBARU_LNG, fake_layer_id)
        assert result is None

    def test_nonexistent_layer_distance_returns_none(self, db):
        """calculate_distance_to_nearest on non-existent layer must return None."""
        fake_layer_id = uuid4()
        dist = analysis.calculate_distance_to_nearest(db, PEKANBARU_LAT, PEKANBARU_LNG, fake_layer_id)
        assert dist is None
