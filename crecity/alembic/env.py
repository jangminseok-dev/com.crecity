import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# crecity/ 와 crecity/apps 를 경로에 올려 core.* 및 앱 ORM(creator...)을 import 가능하게 한다.
# (main.py 의 sys.path.insert(0, "apps") 와 동일 맥락)
_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(_ROOT / "apps"))
sys.path.insert(0, str(_ROOT))

from core.key.secret_manager import get_secret_manager  # noqa: E402

config = context.config
config.set_main_option(
    "sqlalchemy.url",
    get_secret_manager().require("DATABASE_URL").replace(
        "postgresql://", "postgresql+psycopg://"
    ),
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from core.database import Base  # noqa: E402

# 새 ORM 파일을 만들면 여기에 import 한 줄을 추가해야 오토젠 대상이 된다.
import creator.adapter.outbound.orm.creator_profile_orm  # noqa: E402, F401
import creator.adapter.outbound.orm.creator_package_orm  # noqa: E402, F401
import auth.adapter.outbound.orm.user_orm  # noqa: E402, F401
import auth.adapter.outbound.orm.social_identity_orm  # noqa: E402, F401
import auth.adapter.outbound.orm.role_orm  # noqa: E402, F401
import order.adapter.outbound.orm.order_orm  # noqa: E402, F401
import order.adapter.outbound.orm.ledger_entry_orm  # noqa: E402, F401
import payment.adapter.outbound.orm.payment_intent_orm  # noqa: E402, F401

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
