"""add_magic_link_auth

Revision ID: a1b2c3d4e5f6
Revises: 53e3bffc8466
Create Date: 2026-01-15 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '53e3bffc8466'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create magic_links table
    op.create_table('magic_links',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    
    # Alter users table: make name nullable
    op.alter_column('users', 'name', 
        existing_type=sa.String(length=150),
        nullable=True)
    
    # Alter users table: change role from enum to varchar
    # First, add new column
    op.add_column('users', sa.Column('role_temp', sa.String(length=50), nullable=True))
    
    # Copy data from old to new, converting enum values
    op.execute("""
        UPDATE users 
        SET role_temp = CASE 
            WHEN role::text = 'admin' THEN 'admin'
            WHEN role::text = 'developer' THEN 'property_developer'
            ELSE 'property_developer'
        END
    """)
    
    # Drop old column
    op.drop_column('users', 'role')
    
    # Rename new column
    op.alter_column('users', 'role_temp', new_column_name='role')
    
    # Set default and not null
    op.alter_column('users', 'role',
        existing_type=sa.String(length=50),
        nullable=False,
        server_default='property_developer')
    
    # Update auth_provider default
    op.alter_column('users', 'auth_provider',
        existing_type=sa.String(length=50),
        nullable=False,
        server_default='magic_link')


def downgrade() -> None:
    # Revert auth_provider default
    op.alter_column('users', 'auth_provider',
        existing_type=sa.String(length=50),
        nullable=False,
        server_default='local')
    
    # Revert role changes
    op.add_column('users', sa.Column('role_enum', 
        postgresql.ENUM('admin', 'developer', name='userrole', create_type=False),
        nullable=True))
    
    op.execute("""
        UPDATE users 
        SET role_enum = CASE 
            WHEN role = 'admin' THEN 'admin'::userrole
            ELSE 'developer'::userrole
        END
    """)
    
    op.drop_column('users', 'role')
    op.alter_column('users', 'role_enum', new_column_name='role')
    
    # Revert name to not nullable
    op.alter_column('users', 'name',
        existing_type=sa.String(length=150),
        nullable=False)
    
    # Drop magic_links table
    op.drop_table('magic_links')
