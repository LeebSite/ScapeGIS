"""add_gis_features_table

Revision ID: 62fa5f6fc6aa
Revises: f5404bd9a730
Create Date: 2026-01-18 20:06:10.571024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '62fa5f6fc6aa'
down_revision: Union[str, None] = 'f5404bd9a730'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create gis_features table
    op.create_table(
        'gis_features',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('layer_id', sa.UUID(), nullable=False),
        sa.Column('geom', sa.TEXT(), nullable=False),  # Will be converted to Geometry by GeoAlchemy2
        sa.Column('properties', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['layer_id'], ['gis_layers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Enable PostGIS extension if not already enabled
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    
    # Convert geom column to PostGIS geometry type
    op.execute("""
        ALTER TABLE gis_features 
        ALTER COLUMN geom TYPE geometry(GEOMETRY, 4326) 
        USING ST_GeomFromText(geom, 4326)
    """)
    
    # Create spatial index for performance
    op.execute('CREATE INDEX idx_gis_features_geom ON gis_features USING GIST(geom)')
    
    # Create index on layer_id for faster queries
    op.create_index('idx_gis_features_layer_id', 'gis_features', ['layer_id'])


def downgrade() -> None:
    op.drop_index('idx_gis_features_layer_id', table_name='gis_features')
    op.drop_index('idx_gis_features_geom', table_name='gis_features')
    op.drop_table('gis_features')
