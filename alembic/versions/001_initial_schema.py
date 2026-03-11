from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = {row[0] for row in bind.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

    if "accounts" not in tables:
        op.create_table(
            "accounts",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=False, unique=True),
            sa.Column("api_key", sa.String(), nullable=False, unique=True),
            sa.Column("password_hash", sa.String(), nullable=True),
            sa.Column("created_at", sa.String(), nullable=False),
        )
    if "workflow_runs" not in tables:
        op.create_table(
            "workflow_runs",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("created_at", sa.String(), nullable=False),
            sa.Column("account_id", sa.String(), nullable=True),
            sa.Column("source", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("score", sa.Integer(), nullable=False),
            sa.Column("payload_json", sa.Text(), nullable=False),
            sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        )
    if "jobs" not in tables:
        op.create_table(
            "jobs",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("run_id", sa.String(), nullable=False),
            sa.Column("provider", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("detail", sa.String(), nullable=False),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("available_at", sa.String(), nullable=False),
            sa.Column("locked_at", sa.String(), nullable=True),
            sa.Column("locked_by", sa.String(), nullable=True),
            sa.Column("last_error", sa.String(), nullable=True),
            sa.Column("payload_json", sa.Text(), nullable=False),
            sa.Column("created_at", sa.String(), nullable=False),
            sa.Column("updated_at", sa.String(), nullable=False),
            sa.ForeignKeyConstraint(["run_id"], ["workflow_runs.id"]),
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
    op.drop_table("sessions")
    op.drop_table("jobs")
    op.drop_table("workflow_runs")
    op.drop_table("accounts")
