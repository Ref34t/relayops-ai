from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "002_upgrade_existing_tables"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    bind = op.get_bind()
    rows = bind.exec_driver_sql(f"PRAGMA table_info({table_name})").fetchall()
    return {row[1] for row in rows}


def _table_names() -> set[str]:
    bind = op.get_bind()
    rows = bind.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {row[0] for row in rows}


def upgrade() -> None:
    tables = _table_names()
    if "accounts" in tables:
        columns = _column_names("accounts")
        if "password_hash" not in columns:
            op.add_column("accounts", sa.Column("password_hash", sa.String(), nullable=True))

    if "workflow_runs" in tables:
        columns = _column_names("workflow_runs")
        if "account_id" not in columns:
            op.add_column("workflow_runs", sa.Column("account_id", sa.String(), nullable=True))

    if "jobs" in tables:
        columns = _column_names("jobs")
        missing_columns = [
            ("max_attempts", sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3")),
            ("available_at", sa.Column("available_at", sa.String(), nullable=True)),
            ("locked_at", sa.Column("locked_at", sa.String(), nullable=True)),
            ("locked_by", sa.Column("locked_by", sa.String(), nullable=True)),
            ("last_error", sa.Column("last_error", sa.String(), nullable=True)),
        ]
        for name, column in missing_columns:
            if name not in columns:
                op.add_column("jobs", column)
        bind = op.get_bind()
        bind.exec_driver_sql(
            """
            UPDATE jobs
            SET max_attempts = COALESCE(max_attempts, 3),
                available_at = COALESCE(available_at, created_at)
            """
        )

    if "sessions" not in tables:
        op.create_table(
            "sessions",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("account_id", sa.String(), nullable=False),
            sa.Column("created_at", sa.String(), nullable=False),
            sa.Column("expires_at", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        )


def downgrade() -> None:
    pass
