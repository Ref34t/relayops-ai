from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config


def apply_migrations(database_path: Path) -> None:
    base_dir = Path(__file__).resolve().parent.parent
    config = Config(str(base_dir / "alembic.ini"))
    config.set_main_option("script_location", str(base_dir / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")
    command.upgrade(config, "head")
