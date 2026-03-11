from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4

from app.migrations import MigrationManager
from app.models import Account, HealthResponse, JobRecord, NormalizedRecord, WorkflowRun
from app.services import WorkflowEngine


class WorkflowRepository:
    def __init__(self, database_path: Path, demo_api_key: str) -> None:
        self.database_path = database_path
        self.demo_api_key = demo_api_key
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        MigrationManager(self._connect).apply()
        self.ensure_default_account()

    def list_runs(self, account_id: str | None = None) -> list[WorkflowRun]:
        query = """
            SELECT payload_json
            FROM workflow_runs
        """
        params: tuple = ()
        if account_id:
            query += " WHERE account_id = ?"
            params = (account_id,)
        query += " ORDER BY datetime(created_at) DESC, rowid DESC"
        with closing(self._connect()) as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._deserialize_run(row["payload_json"]) for row in rows]

    def save_run(self, run: WorkflowRun) -> WorkflowRun:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO workflow_runs (id, created_at, account_id, source, status, score, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.id,
                    run.created_at.isoformat(),
                    run.account_id,
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

    def get_run(self, run_id: str) -> WorkflowRun | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT payload_json FROM workflow_runs WHERE id = ?",
                (run_id,),
            ).fetchone()
        if not row:
            return None
        return self._deserialize_run(row["payload_json"])

    def ensure_default_account(self) -> Account:
        account = self.get_account_by_api_key(self.demo_api_key)
        if account:
            return account
        account = Account(
            id=str(uuid4())[:8],
            name="RelayOps Demo Workspace",
            email="demo@relayops.app",
            api_key=self.demo_api_key,
        )
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO accounts (id, name, email, api_key, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (account.id, account.name, account.email, account.api_key, account.created_at.isoformat()),
            )
            connection.commit()
        return account

    def get_default_account(self) -> Account:
        account = self.get_account_by_api_key(self.demo_api_key)
        if not account:
            return self.ensure_default_account()
        return account

    def create_account(self, name: str, email: str, api_key: str) -> Account:
        account = Account(id=str(uuid4())[:8], name=name, email=email, api_key=api_key)
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO accounts (id, name, email, api_key, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (account.id, account.name, account.email, account.api_key, account.created_at.isoformat()),
            )
            connection.commit()
        return account

    def get_account_by_api_key(self, api_key: str) -> Account | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT id, name, email, api_key, created_at FROM accounts WHERE api_key = ?",
                (api_key,),
            ).fetchone()
        if not row:
            return None
        return Account.model_validate(dict(row))

    def enqueue_job(self, run_id: str, provider: str) -> JobRecord:
        job = JobRecord(
            id=str(uuid4())[:8],
            run_id=run_id,
            provider=provider,
            status="pending",
            detail=f"{provider} job queued.",
        )
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO jobs (id, run_id, provider, status, detail, attempts, payload_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.run_id,
                    job.provider,
                    job.status,
                    job.detail,
                    job.attempts,
                    job.model_dump_json(),
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                ),
            )
            connection.commit()
        return job

    def claim_next_job(self, run_id: str) -> JobRecord | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT payload_json
                FROM jobs
                WHERE run_id = ? AND status = 'pending'
                ORDER BY datetime(created_at) ASC, rowid ASC
                LIMIT 1
                """,
                (run_id,),
            ).fetchone()
            if not row:
                return None
            job = JobRecord.model_validate_json(row["payload_json"])
            job.status = "processing"
            job.attempts += 1
            connection.execute(
                """
                UPDATE jobs
                SET status = ?, attempts = ?, detail = ?, updated_at = ?, payload_json = ?
                WHERE id = ?
                """,
                ("processing", job.attempts, "Job claimed by worker.", job.updated_at.isoformat(), job.model_dump_json(), job.id),
            )
            connection.commit()
        return job

    def complete_job(self, job_id: str, status: str, detail: str) -> None:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT payload_json FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return
            job = JobRecord.model_validate_json(row["payload_json"])
            job.status = status
            job.detail = detail
            connection.execute(
                """
                UPDATE jobs
                SET status = ?, detail = ?, updated_at = ?, payload_json = ?
                WHERE id = ?
                """,
                (job.status, job.detail, job.updated_at.isoformat(), job.model_dump_json(), job.id),
            )
            connection.commit()

    def list_jobs(self, account_id: str | None = None, run_id: str | None = None) -> list[JobRecord]:
        query = """
            SELECT jobs.payload_json
            FROM jobs
            JOIN workflow_runs ON workflow_runs.id = jobs.run_id
        """
        params: tuple = ()
        clauses: list[str] = []
        if account_id:
            clauses.append("workflow_runs.account_id = ?")
            params += (account_id,)
        if run_id:
            clauses.append("jobs.run_id = ?")
            params = (run_id,)
            if account_id:
                params = (account_id, run_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY datetime(jobs.created_at) DESC, jobs.rowid DESC"
        with closing(self._connect()) as connection:
            rows = connection.execute(query, params).fetchall()
        return [JobRecord.model_validate_json(row["payload_json"]) for row in rows]

    def list_pending_run_ids(self) -> list[str]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT run_id
                FROM jobs
                WHERE status IN ('pending', 'processing')
                ORDER BY datetime(created_at) ASC, rowid ASC
                """
            ).fetchall()
        return [row["run_id"] for row in rows]

    def finalize_run_status(self, run_id: str) -> None:
        run = self.get_run(run_id)
        if not run:
            return
        jobs = self.list_jobs(run_id)
        if any(job.status == "pending" for job in jobs):
            run.status = "queued"
        elif any(job.status == "failed" for job in jobs):
            run.status = "degraded"
        else:
            run.status = "completed"
        self.save_run(run)

    def _deserialize_run(self, payload_json: str) -> WorkflowRun:
        payload = json.loads(payload_json)
        if "ai_analysis" not in payload:
            normalized = NormalizedRecord.model_validate(payload["normalized"])
            payload["ai_analysis"] = WorkflowEngine.build_ai_analysis(
                normalized,
                payload["score"],
            ).model_dump()
        return WorkflowRun.model_validate(payload)

    def health(self, account_id: str | None = None) -> HealthResponse:
        params: tuple = ()
        runs_where = ""
        jobs_where = ""
        if account_id:
            runs_where = " WHERE account_id = ?"
            jobs_where = " WHERE workflow_runs.account_id = ? AND jobs.status IN ('pending', 'processing')"
            params = (account_id,)
        with closing(self._connect()) as connection:
            row = connection.execute(
                f"""
                SELECT
                    COUNT(*) AS total_runs,
                    SUM(CASE WHEN status IN ('completed', 'degraded') THEN 1 ELSE 0 END) AS completed_runs
                FROM workflow_runs
                {runs_where}
                """,
                params,
            ).fetchone()
            sync_targets = connection.execute(
                f"""
                SELECT COALESCE(SUM(json_array_length(json_extract(payload_json, '$.sync_results'))), 0) AS sync_targets
                FROM workflow_runs
                {runs_where}
                """,
                params,
            ).fetchone()
            queued_jobs = connection.execute(
                f"""
                SELECT COUNT(*) AS queued_jobs
                FROM jobs
                JOIN workflow_runs ON workflow_runs.id = jobs.run_id
                {jobs_where or "WHERE jobs.status IN ('pending', 'processing')"}
                """,
                params if account_id else (),
            ).fetchone()
        return HealthResponse(
            status="healthy" if int(queued_jobs["queued_jobs"] or 0) == 0 else "busy",
            database=str(self.database_path),
            total_runs=int(row["total_runs"] or 0),
            completed_runs=int(row["completed_runs"] or 0),
            sync_targets=int(sync_targets["sync_targets"] or 0),
        )
