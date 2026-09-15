"""add_gis_tables

Revision ID: f5404bd9a730
Revises: b1c2d3e4f5g6
Create Date: 2026-01-18 02:41:29.255559

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f5404bd9a730'
down_revision: Union[str, None] = 'b1c2d3e4f5g6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create new GIS tables and drop old ones
    """
    
    # First, drop all old GIS tables with prefix gis_59f8a6ac_dot_*
    # Get connection to execute raw SQL
    conn = op.get_bind()
    
    # Query to get all tables with the old GIS prefix
    result = conn.execute(sa.text("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename LIKE 'gis_%_dot_%'
    """))
    
    # Drop each old table
    for row in result:
        table_name = row[0]
        print(f"Dropping old table: {table_name}")
        op.drop_table(table_name)
    
    # Create gis_datasets table
    op.create_table('gis_datasets',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('original_filename', sa.String(length=500), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_path', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('bbox', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('crs', sa.String(length=50), nullable=True),
        sa.Column('srid', sa.Integer(), nullable=True, server_default='4326'),
        sa.Column('geometry_type', sa.String(length=20), nullable=True),
        sa.Column('total_layers', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_features', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_gis_datasets_user_id', 'gis_datasets', ['user_id'])
    op.create_index('idx_gis_datasets_status', 'gis_datasets', ['status'])
    
    # Create gis_layers table
    op.create_table('gis_layers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('dataset_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('geometry_type', sa.String(length=50), nullable=True),
        sa.Column('feature_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('bbox', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('crs', sa.String(length=50), nullable=True),
        sa.Column('geojson_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('full_geojson_path', sa.Text(), nullable=True),
        sa.Column('style', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('properties_schema', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_visible', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('layer_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('extra_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['gis_datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_gis_layers_dataset_id', 'gis_layers', ['dataset_id'])
    op.create_index('idx_gis_layers_layer_order', 'gis_layers', ['layer_order'])


def downgrade() -> None:
    """
    Drop GIS tables
    """
    # Drop indexes first
    op.drop_index('idx_gis_layers_layer_order', 'gis_layers')
    op.drop_index('idx_gis_layers_dataset_id', 'gis_layers')
    op.drop_index('idx_gis_datasets_status', 'gis_datasets')
    op.drop_index('idx_gis_datasets_user_id', 'gis_datasets')
    
    # Drop tables (layers first due to foreign key)
    op.drop_table('gis_layers')
    op.drop_table('gis_datasets')

