from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# Import Base and all models
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import Base
# Import all models to register them with Base
from app.models.user import User
from app.models.incident import Incident
from app.models.auth import (
    Role, Permission, UserSession, TwoFactorAuth,
    VerificationCode, AuditLog, Alert,
    user_roles, role_permissions
)

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def include_object(object, name, type_, reflected, compare_to):
    """
    Exclude PostGIS and other system tables from migrations
    """
    # Exclude PostGIS tiger geocoder tables
    if type_ == "table" and name in [
        'spatial_ref_sys', 'geometry_columns', 'geography_columns', 'raster_columns', 'raster_overviews',
        'topology', 'layer', 'tabblock', 'tabblock20', 'bg', 'cousub', 'county', 'county_lookup',
        'countysub_lookup', 'direction_lookup', 'edges', 'faces', 'featnames', 'geocode_settings',
        'geocode_settings_default', 'loader_lookuptables', 'loader_platform', 'loader_variables',
        'pagc_gaz', 'pagc_lex', 'pagc_rules', 'place', 'place_lookup', 'secondary_unit_lookup',
        'state', 'state_lookup', 'street_type_lookup', 'tract', 'zcta5', 'zip_lookup', 'zip_lookup_all',
        'zip_lookup_base', 'zip_state', 'zip_state_loc', 'addr', 'addrfeat'
    ]:
        return False
    # Exclude PostGIS extension tables that we don't manage
    if type_ == "table" and (name.startswith('tiger_') or name.startswith('us_')):
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
