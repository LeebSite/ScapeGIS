"""redesign_auth_system

Revision ID: b1c2d3e4f5g6
Revises: a1b2c3d4e5f6
Create Date: 2026-01-15 19:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5g6'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create email_verifications table
    op.create_table('email_verifications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=150), nullable=False),
        sa.Column('code', sa.String(length=6), nullable=False),
        sa.Column('temp_password_hash', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_email_verifications_email', 'email_verifications', ['email'])
    op.create_index('idx_email_verifications_code', 'email_verifications', ['code'])
    
    # Add birthday column to users
    op.add_column('users', sa.Column('birthday', sa.Date(), nullable=True))
    
    # Create enum type if it doesn't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE userrole AS ENUM ('admin', 'developer');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Add new role column with enum type
    op.add_column('users', sa.Column('role_new', postgresql.ENUM('admin', 'developer', name='userrole', create_type=False), nullable=True))
    
    # Migrate data - Set all users to DEVELOPER role (uppercase to match existing enum)
    op.execute("""
        UPDATE users 
        SET role_new = 'DEVELOPER'::userrole
    """)
    
    # Drop old column
    op.drop_column('users', 'role')
    
    # Rename new column
    op.alter_column('users', 'role_new', new_column_name='role')
    
    # Set NOT NULL and default
    op.alter_column('users', 'role',
        existing_type=postgresql.ENUM('admin', 'developer', name='userrole', create_type=False),
        nullable=False,
        server_default='DEVELOPER')
    
    # Update auth_provider default
    op.alter_column('users', 'auth_provider',
        existing_type=sa.String(length=50),
        nullable=False,
        server_default='local')


def downgrade() -> None:
    # Revert auth_provider default
    op.alter_column('users', 'auth_provider',
        existing_type=sa.String(length=50),
        nullable=False,
        server_default='magic_link')
    
    # Convert role back to string
    op.add_column('users', sa.Column('role_str', sa.String(length=50), nullable=True))
    
    op.execute("""
        UPDATE users 
        SET role_str = CASE 
            WHEN role::text = 'admin' THEN 'admin'
            WHEN role::text = 'developer' THEN 'property_developer'
            ELSE 'property_developer'
        END
    """)
    
    op.drop_column('users', 'role')
    op.alter_column('users', 'role_str', new_column_name='role')
    
    op.alter_column('users', 'role',
        existing_type=sa.String(length=50),
        nullable=False,
        server_default='property_developer')
    
    # Drop enum type
    postgresql.ENUM(name='userrole').drop(op.get_bind(), checkfirst=True)
    
    # Remove birthday
    op.drop_column('users', 'birthday')
    
    # Drop email_verifications table
    op.drop_index('idx_email_verifications_code', 'email_verifications')
    op.drop_index('idx_email_verifications_email', 'email_verifications')
    op.drop_table('email_verifications')
