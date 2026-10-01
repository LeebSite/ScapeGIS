"""add_project_tables

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-10-01 22:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b4c5d6e7f8a9"
down_revision: Union[str, None] = "a3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # ENUM types
    # ------------------------------------------------------------------ #
    project_type_enum = postgresql.ENUM(
        "RESIDENTIAL", "COMMERCIAL", "INDUSTRIAL", "MIXED_USE", "OTHER",
        name="projecttype"
    )
    project_type_enum.create(op.get_bind())

    project_status_enum = postgresql.ENUM(
        "DRAFT", "ACTIVE", "ARCHIVED",
        name="projectstatus"
    )
    project_status_enum.create(op.get_bind())

    # ------------------------------------------------------------------ #
    # projects
    # ------------------------------------------------------------------ #
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "project_type",
            postgresql.ENUM("RESIDENTIAL", "COMMERCIAL", "INDUSTRIAL", "MIXED_USE", "OTHER",
                            name="projecttype", create_type=False),
            nullable=False,
            server_default="OTHER",
        ),
        sa.Column("city", sa.String(255), nullable=True),
        sa.Column("province", sa.String(255), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("DRAFT", "ACTIVE", "ARCHIVED",
                            name="projectstatus", create_type=False),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_projects_workspace_id", "projects", ["workspace_id"])
    op.create_index("ix_projects_created_by", "projects", ["created_by"])
    op.create_index("ix_projects_status", "projects", ["status"])

    # ------------------------------------------------------------------ #
    # project_layers
    # ------------------------------------------------------------------ #
    op.create_table(
        "project_layers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "dataset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("gis_datasets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "layer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("gis_layers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("opacity", sa.Float(), nullable=False, server_default=sa.text("1.0")),
        sa.Column("layer_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("project_id", "layer_id", name="uq_project_layer"),
    )
    op.create_index("ix_project_layers_project_id", "project_layers", ["project_id"])
    op.create_index("ix_project_layers_layer_id", "project_layers", ["layer_id"])


def downgrade() -> None:
    op.drop_index("ix_project_layers_layer_id", table_name="project_layers")
    op.drop_index("ix_project_layers_project_id", table_name="project_layers")
    op.drop_table("project_layers")

    op.drop_index("ix_projects_status", table_name="projects")
    op.drop_index("ix_projects_created_by", table_name="projects")
    op.drop_index("ix_projects_workspace_id", table_name="projects")
    op.drop_table("projects")

    op.execute("DROP TYPE IF EXISTS projectstatus")
    op.execute("DROP TYPE IF EXISTS projecttype")
