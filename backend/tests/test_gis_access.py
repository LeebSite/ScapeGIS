import pytest
import uuid
from fastapi import HTTPException
from app.db.session import SessionLocal
from app.db.models.user import User, UserRole
from app.db.models.workspace import Workspace
from app.db.models.workspace_member import WorkspaceMember, WorkspaceMemberRole
from app.db.models.gis_dataset import GISDataset
from app.db.models.gis_layer import GISLayer
from app.db.models.project import Project, ProjectType, ProjectStatus
from app.db.models.workspace_gis_access import WorkspaceGISAccess
from app.schemas.gis_access_schema import GISAccessGrantRequest, GISAccessRevokeRequest
from app.schemas.project_schema import ProjectLayerAddRequest
from app.services import gis_access_service
from app.services import project_service
from app.repositories import gis_access_repository as access_repo


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def setup_data(db):
    uid = uuid.uuid4().hex[:8]

    # 1. Admin user
    admin_user = User(
        email=f"admin_{uid}@test.com",
        name=f"Admin {uid}",
        role=UserRole.ADMIN,
        is_active=True,
    )
    # 2. Developer 1 (owner of Workspace A)
    dev1 = User(
        email=f"dev1_{uid}@test.com",
        name=f"Dev One {uid}",
        role=UserRole.DEVELOPER,
        is_active=True,
    )
    # 3. Developer 2 (owner of Workspace B)
    dev2 = User(
        email=f"dev2_{uid}@test.com",
        name=f"Dev Two {uid}",
        role=UserRole.DEVELOPER,
        is_active=True,
    )
    db.add_all([admin_user, dev1, dev2])
    db.commit()
    db.refresh(admin_user)
    db.refresh(dev1)
    db.refresh(dev2)

    # 4. Workspace A
    ws_a = Workspace(
        name=f"Workspace A {uid}",
        slug=f"ws-a-{uid}",
        owner_id=dev1.id,
    )
    # 5. Workspace B
    ws_b = Workspace(
        name=f"Workspace B {uid}",
        slug=f"ws-b-{uid}",
        owner_id=dev2.id,
    )
    db.add_all([ws_a, ws_b])
    db.commit()
    db.refresh(ws_a)
    db.refresh(ws_b)

    # Add members
    mem_a = WorkspaceMember(
        workspace_id=ws_a.id,
        user_id=dev1.id,
        role=WorkspaceMemberRole.OWNER,
    )
    mem_b = WorkspaceMember(
        workspace_id=ws_b.id,
        user_id=dev2.id,
        role=WorkspaceMemberRole.OWNER,
    )
    db.add_all([mem_a, mem_b])
    db.commit()

    # 6. GIS Dataset (Platform Asset)
    dataset = GISDataset(
        user_id=admin_user.id,
        name=f"Kota Pekanbaru {uid}",
        original_filename="pekanbaru.zip",
        file_type="shapefile",
        status="completed",
        total_layers=1,
        total_features=10,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    layer = GISLayer(
        dataset_id=dataset.id,
        name="Batas Administrasi",
        geometry_type="Polygon",
        is_visible=True,
        layer_order=0,
    )
    db.add(layer)
    db.commit()
    db.refresh(layer)

    # 7. Project inside Workspace A
    project_a = Project(
        workspace_id=ws_a.id,
        created_by=dev1.id,
        name=f"Project A {uid}",
        project_type=ProjectType.RESIDENTIAL,
        status=ProjectStatus.ACTIVE,
    )
    db.add(project_a)
    db.commit()
    db.refresh(project_a)

    yield {
        "admin": admin_user,
        "dev1": dev1,
        "dev2": dev2,
        "ws_a": ws_a,
        "ws_b": ws_b,
        "dataset": dataset,
        "layer": layer,
        "project_a": project_a,
    }

    # Cleanup
    db.query(WorkspaceGISAccess).filter(WorkspaceGISAccess.dataset_id == dataset.id).delete()
    db.query(Project).filter(Project.id == project_a.id).delete()
    db.query(GISLayer).filter(GISLayer.id == layer.id).delete()
    db.query(GISDataset).filter(GISDataset.id == dataset.id).delete()
    db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id.in_([ws_a.id, ws_b.id])).delete()
    db.query(Workspace).filter(Workspace.id.in_([ws_a.id, ws_b.id])).delete()
    db.query(User).filter(User.id.in_([admin_user.id, dev1.id, dev2.id])).delete()
    db.commit()


def test_non_admin_cannot_grant_access(db, setup_data):
    """Rule 2: Non-admin cannot grant GIS access."""
    req = GISAccessGrantRequest(
        workspace_id=setup_data["ws_a"].id,
        dataset_id=setup_data["dataset"].id,
    )
    with pytest.raises(HTTPException) as exc:
        gis_access_service.grant_dataset_access(
            db=db,
            current_user=setup_data["dev1"],
            payload=req,
        )
    assert exc.value.status_code == 403


def test_admin_can_grant_access(db, setup_data):
    """Rule 1: Admin can grant GIS access."""
    req = GISAccessGrantRequest(
        workspace_id=setup_data["ws_a"].id,
        dataset_id=setup_data["dataset"].id,
        notes="Official grant for Pekanbaru planning",
    )
    grant = gis_access_service.grant_dataset_access(
        db=db,
        current_user=setup_data["admin"],
        payload=req,
    )
    assert grant.is_active is True
    assert grant.workspace_id == setup_data["ws_a"].id
    assert grant.dataset_id == setup_data["dataset"].id

    # Verify via repository
    assert access_repo.is_accessible(db, setup_data["ws_a"].id, setup_data["dataset"].id) is True


def test_duplicate_grant_handled_safely(db, setup_data):
    """Rule 9: Duplicate grant is rejected / handled safely without errors."""
    req = GISAccessGrantRequest(
        workspace_id=setup_data["ws_a"].id,
        dataset_id=setup_data["dataset"].id,
    )
    # Granting again should return existing grant safely
    grant = gis_access_service.grant_dataset_access(
        db=db,
        current_user=setup_data["admin"],
        payload=req,
    )
    assert grant.is_active is True


def test_workspace_member_can_access_granted_dataset(db, setup_data):
    """Rule 5: Workspace member can access granted dataset."""
    datasets = gis_access_service.get_authorized_datasets_for_workspace(
        db=db,
        workspace_id=setup_data["ws_a"].id,
        current_user=setup_data["dev1"],
    )
    dataset_ids = [d.id for d in datasets]
    assert setup_data["dataset"].id in dataset_ids


def test_cross_workspace_gis_access_blocked(db, setup_data):
    """Rule 6, 7 & 8: Cross-workspace access is blocked."""
    # Workspace B was NOT granted access to this dataset
    assert access_repo.is_accessible(db, setup_data["ws_b"].id, setup_data["dataset"].id) is False

    # Dev 2 in Workspace B sees empty or does not see Workspace A's granted dataset
    datasets_b = gis_access_service.get_authorized_datasets_for_workspace(
        db=db,
        workspace_id=setup_data["ws_b"].id,
        current_user=setup_data["dev2"],
    )
    dataset_ids_b = [d.id for d in datasets_b]
    assert setup_data["dataset"].id not in dataset_ids_b

    # Dev 2 cannot access Workspace A's GIS (non-member forbidden)
    with pytest.raises(HTTPException) as exc:
        gis_access_service.get_authorized_datasets_for_workspace(
            db=db,
            workspace_id=setup_data["ws_a"].id,
            current_user=setup_data["dev2"],
        )
    assert exc.value.status_code == 403


def test_project_can_add_authorized_layer(db, setup_data):
    """Rule 14: Project inside Workspace A can add layers from authorized GIS dataset."""
    layer_req = ProjectLayerAddRequest(
        dataset_id=setup_data["dataset"].id,
        layer_id=setup_data["layer"].id,
        is_visible=True,
        opacity=1.0,
    )
    pl = project_service.add_project_layer(
        db=db,
        project_id=setup_data["project_a"].id,
        current_user=setup_data["dev1"],
        payload=layer_req,
        request=None,
    )
    assert pl.dataset_id == setup_data["dataset"].id
    assert pl.layer_id == setup_data["layer"].id


def test_non_admin_cannot_revoke_access(db, setup_data):
    """Rule 4: Non-admin cannot revoke GIS access."""
    req = GISAccessRevokeRequest(
        workspace_id=setup_data["ws_a"].id,
        dataset_id=setup_data["dataset"].id,
    )
    with pytest.raises(HTTPException) as exc:
        gis_access_service.revoke_dataset_access(
            db=db,
            current_user=setup_data["dev1"],
            payload=req,
        )
    assert exc.value.status_code == 403


def test_admin_can_revoke_access_and_dataset_remains_intact(db, setup_data):
    """Rule 3, 10, 11 & 12: Admin revokes access; entitlement removed, GIS dataset remains intact."""
    req = GISAccessRevokeRequest(
        workspace_id=setup_data["ws_a"].id,
        dataset_id=setup_data["dataset"].id,
        reason="Subscription ended",
    )
    revoked = gis_access_service.revoke_dataset_access(
        db=db,
        current_user=setup_data["admin"],
        payload=req,
    )
    assert revoked.is_active is False
    assert revoked.revoked_at is not None

    # Entitlement is now removed
    assert access_repo.is_accessible(db, setup_data["ws_a"].id, setup_data["dataset"].id) is False

    # Workspace A member now sees no authorized dataset
    datasets = gis_access_service.get_authorized_datasets_for_workspace(
        db=db,
        workspace_id=setup_data["ws_a"].id,
        current_user=setup_data["dev1"],
    )
    assert setup_data["dataset"].id not in [d.id for d in datasets]

    # CRITICAL: GIS dataset itself is NOT deleted and remains intact!
    ds = db.query(GISDataset).filter(GISDataset.id == setup_data["dataset"].id).first()
    assert ds is not None
    assert ds.name == setup_data["dataset"].name