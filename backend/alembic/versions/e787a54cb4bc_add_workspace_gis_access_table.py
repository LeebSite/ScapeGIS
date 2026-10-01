"""add_workspace_gis_access_table

Revision ID: e787a54cb4bc
Revises: b4c5d6e7f8a9
Create Date: 2026-10-02 00:31:17.191708

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e787a54cb4bc'
down_revision: Union[str, None] = 'b4c5d6e7f8a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'workspace_gis_access',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'workspace_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('workspaces.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column(
            'dataset_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('gis_datasets.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column(
            'granted_by',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True
        ),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.UniqueConstraint('workspace_id', 'dataset_id', name='uq_workspace_gis_access')
    )
    op.create_index('ix_workspace_gis_access_workspace_id', 'workspace_gis_access', ['workspace_id'], unique=False)
    op.create_index('ix_workspace_gis_access_dataset_id', 'workspace_gis_access', ['dataset_id'], unique=False)
    op.create_index('ix_workspace_gis_access_is_active', 'workspace_gis_access', ['is_active'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_workspace_gis_access_is_active', table_name='workspace_gis_access')
    op.drop_index('ix_workspace_gis_access_dataset_id', table_name='workspace_gis_access')
    op.drop_index('ix_workspace_gis_access_workspace_id', table_name='workspace_gis_access')
    op.drop_table('workspace_gis_access')