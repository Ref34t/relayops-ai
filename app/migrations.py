from __future__ import annotations

from contextlib import closing
import sqlite3


MIGRATIONS: list[tuple[str, str]] = [
    (
        "001_initial_schema",
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            api_key TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS workflow_runs (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            account_id TEXT,
            source TEXT NOT NULL,
            status TEXT NOT NULL,
            score INTEGER NOT NULL,
            payload_json TEXT NOT NULL,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        );

        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            status TEXT NOT NULL,
            detail TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES workflow_runs (id)
        );
        """,
    ),
    (
        "002_workflow_runs_account_id",
        """
        ALTER TABLE workflow_runs ADD COLUMN account_id TEXT;
        """,
    ),
]


class MigrationManager:
    def __init__(self, connection_factory) -> None:
        self.connection_factory = connection_factory

    def apply(self) -> None:
        with closing(self.connection_factory()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            applied = {
                row[0]
                for row in connection.execute("SELECT version FROM schema_migrations").fetchall()
            }
            for version, sql in MIGRATIONS:
                if version in applied:
                    continue
                try:
                    connection.executescript(sql)
                except sqlite3.OperationalError as exc:
                    if "duplicate column name" not in str(exc).lower():
                        raise
                connection.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
            connection.commit()
