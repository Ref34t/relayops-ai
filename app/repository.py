from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from app.models import HealthResponse, WorkflowRun


class WorkflowRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    payload_json TEXT NOT NULL
                );
                """
            )
            connection.commit()

    def list_runs(self) -> list[WorkflowRun]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT payload_json
                FROM workflow_runs
                ORDER BY datetime(created_at) DESC, rowid DESC
                """
            ).fetchall()
        return [WorkflowRun.model_validate_json(row["payload_json"]) for row in rows]

    def save_run(self, run: WorkflowRun) -> WorkflowRun:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO workflow_runs (id, created_at, source, status, score, payload_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    run.id,
                    run.created_at.isoformat(),
                    run.source,
                    run.status,
                    run.score,
                    run.model_dump_json(),
                ),
            )
            connection.commit()
        return run

    def has_runs(self) -> bool:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM workflow_runs").fetchone()
        return bool(row["count"])

    def health(self) -> HealthResponse:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS total_runs,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_runs
                FROM workflow_runs
                """
            ).fetchone()
            sync_targets = connection.execute(
                """
                SELECT COALESCE(SUM(json_array_length(json_extract(payload_json, '$.sync_results'))), 0) AS sync_targets
                FROM workflow_runs
                """
            ).fetchone()
        return HealthResponse(
            status="healthy",
            database=str(self.database_path),
            total_runs=int(row["total_runs"] or 0),
            completed_runs=int(row["completed_runs"] or 0),
            sync_targets=int(sync_targets["sync_targets"] or 0),
        )
