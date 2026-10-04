from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

from app.db.base import Base

# Alembic Config
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.core.config import settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Import all models so Alembic can detect them
from app.db.models import (
    User, OAuthAccount, RefreshToken, AuditLog,
    Permission, RolePermission, UserPermission,
    Session, MagicLink, EmailVerification,
    GISDataset, GISLayer, GISFeature,
    Workspace, WorkspaceMember, WorkspaceInvitation,
    Project, ProjectLayer, WorkspaceGISAccess,
    LayerSemantic
)

# Target metadata for 'autogenerate'
target_metadata = Base.metadata


# Exclude PostGIS system tables
def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name == "spatial_ref_sys":
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_object=include_object,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()