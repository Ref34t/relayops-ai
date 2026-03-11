from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from app.auth import hash_password
from app.migrations import apply_migrations
from app.models import Account, HealthResponse, JobRecord, NormalizedRecord, SessionRecord, WorkflowRun, utc_now
from app.services import WorkflowEngine


class WorkflowRepository:
    def __init__(self, database_path: Path, demo_api_key: str, demo_email: str, demo_password: str) -> None:
        self.database_path = database_path
        self.demo_api_key = demo_api_key
        self.demo_email = demo_email
        self.demo_password = demo_password
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        apply_migrations(self.database_path)
        self.ensure_default_account()

    def list_runs(self, account_id: str | None = None) -> list[WorkflowRun]:
        query = "SELECT payload_json FROM workflow_runs"
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
            row = connection.execute("SELECT payload_json FROM workflow_runs WHERE id = ?", (run_id,)).fetchone()
        if not row:
            return None
        return self._deserialize_run(row["payload_json"])

    def ensure_default_account(self) -> Account:
        account = self.get_account_by_email(self.demo_email)
        password_hash = hash_password(self.demo_password)
        if account:
            needs_update = account.api_key != self.demo_api_key or not account.password_hash
            if needs_update:
                with closing(self._connect()) as connection:
                    connection.execute(
                        "UPDATE accounts SET api_key = ?, password_hash = ? WHERE id = ?",
                        (self.demo_api_key, password_hash, account.id),
                    )
                    connection.commit()
                account.api_key = self.demo_api_key
                account.password_hash = password_hash
            return account

        account = Account(
            id=str(uuid4())[:8],
            name="RelayOps Demo Workspace",
            email=self.demo_email,
            api_key=self.demo_api_key,
            password_hash=password_hash,
        )
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO accounts (id, name, email, api_key, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (account.id, account.name, account.email, account.api_key, account.password_hash, account.created_at.isoformat()),
            )
            connection.commit()
        return account

    def get_default_account(self) -> Account:
        account = self.get_account_by_email(self.demo_email)
        if not account:
            return self.ensure_default_account()
        return account

    def create_account(self, name: str, email: str, api_key: str, password: str | None = None) -> Account:
        account = Account(
            id=str(uuid4())[:8],
            name=name,
            email=email.lower(),
            api_key=api_key,
            password_hash=hash_password(password) if password else None,
        )
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO accounts (id, name, email, api_key, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (account.id, account.name, account.email, account.api_key, account.password_hash, account.created_at.isoformat()),
            )
            connection.commit()
        return account

    def get_account_by_id(self, account_id: str) -> Account | None:
        return self._get_account("SELECT id, name, email, api_key, password_hash, created_at FROM accounts WHERE id = ?", (account_id,))

    def get_account_by_api_key(self, api_key: str) -> Account | None:
        return self._get_account(
            "SELECT id, name, email, api_key, password_hash, created_at FROM accounts WHERE api_key = ?",
            (api_key,),
        )

    def get_account_by_email(self, email: str) -> Account | None:
        return self._get_account(
            "SELECT id, name, email, api_key, password_hash, created_at FROM accounts WHERE email = ?",
            (email.lower(),),
        )

    def _get_account(self, query: str, params: tuple) -> Account | None:
        with closing(self._connect()) as connection:
            row = connection.execute(query, params).fetchone()
        if not row:
            return None
        return Account.model_validate(dict(row))

    def create_session(self, account_id: str, expires_at) -> SessionRecord:
        session = SessionRecord(id=str(uuid4()), account_id=account_id, expires_at=expires_at)
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO sessions (id, account_id, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (session.id, session.account_id, session.created_at.isoformat(), session.expires_at.isoformat()),
            )
            connection.commit()
        return session

    def delete_session(self, session_id: str) -> None:
        with closing(self._connect()) as connection:
            connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            connection.commit()

    def get_account_by_session(self, session_id: str) -> Account | None:
        now = utc_now().isoformat()
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT accounts.id, accounts.name, accounts.email, accounts.api_key, accounts.password_hash, accounts.created_at
                FROM sessions
                JOIN accounts ON accounts.id = sessions.account_id
                WHERE sessions.id = ? AND sessions.expires_at > ?
                """,
                (session_id, now),
            ).fetchone()
        if not row:
            return None
        return Account.model_validate(dict(row))

    def purge_expired_sessions(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (utc_now().isoformat(),))
            connection.commit()

    def enqueue_job(self, run_id: str, provider: str, max_attempts: int = 3) -> JobRecord:
        now = utc_now()
        job = JobRecord(
            id=str(uuid4())[:8],
            run_id=run_id,
            provider=provider,
            status="pending",
            detail=f"{provider} job queued.",
            max_attempts=max_attempts,
            available_at=now,
        )
        with closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO jobs (
                    id, run_id, provider, status, detail, attempts, max_attempts, available_at,
                    locked_at, locked_by, last_error, payload_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.run_id,
                    job.provider,
                    job.status,
                    job.detail,
                    job.attempts,
                    job.max_attempts,
                    job.available_at.isoformat(),
                    job.locked_at.isoformat() if job.locked_at else None,
                    job.locked_by,
                    job.last_error,
                    job.model_dump_json(),
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                ),
            )
            connection.commit()
        return job

    def claim_next_job(self, run_id: str, worker_id: str) -> JobRecord | None:
        now = utc_now()
        stale_before = (now - timedelta(minutes=5)).isoformat()
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT payload_json
                FROM jobs
                WHERE run_id = ?
                  AND (
                    (status = 'pending' AND available_at <= ?)
                    OR (status = 'processing' AND locked_at <= ?)
                  )
                ORDER BY datetime(available_at) ASC, rowid ASC
                LIMIT 1
                """,
                (run_id, now.isoformat(), stale_before),
            ).fetchone()
            if not row:
                return None
            job = JobRecord.model_validate_json(row["payload_json"])
            job.status = "processing"
            job.attempts += 1
            job.locked_at = now
            job.locked_by = worker_id
            job.updated_at = now
            job.detail = f"Claimed by worker {worker_id}."
            connection.execute(
                """
                UPDATE jobs
                SET status = ?, attempts = ?, detail = ?, available_at = ?, locked_at = ?, locked_by = ?, last_error = ?, updated_at = ?, payload_json = ?
                WHERE id = ?
                """,
                (
                    job.status,
                    job.attempts,
                    job.detail,
                    job.available_at.isoformat(),
                    job.locked_at.isoformat(),
                    job.locked_by,
                    job.last_error,
                    job.updated_at.isoformat(),
                    job.model_dump_json(),
                    job.id,
                ),
            )
            connection.commit()
        return job

    def complete_job(self, job_id: str, status: str, detail: str) -> None:
        self._update_job(job_id, status=status, detail=detail, locked_at=None, locked_by=None, last_error=None)

    def fail_job(self, job_id: str, detail: str, retry_delay_seconds: int = 5) -> None:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT payload_json FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return
            job = JobRecord.model_validate_json(row["payload_json"])
            now = utc_now()
            terminal = job.attempts >= job.max_attempts
            job.status = "failed" if terminal else "pending"
            job.detail = detail
            job.last_error = detail
            job.available_at = now if terminal else now + timedelta(seconds=retry_delay_seconds * max(job.attempts, 1))
            job.locked_at = None
            job.locked_by = None
            job.updated_at = now
            connection.execute(
                """
                UPDATE jobs
                SET status = ?, detail = ?, available_at = ?, locked_at = ?, locked_by = ?, last_error = ?, updated_at = ?, payload_json = ?
                WHERE id = ?
                """,
                (
                    job.status,
                    job.detail,
                    job.available_at.isoformat(),
                    job.locked_at,
                    job.locked_by,
                    job.last_error,
                    job.updated_at.isoformat(),
                    job.model_dump_json(),
                    job.id,
                ),
            )
            connection.commit()

    def _update_job(
        self,
        job_id: str,
        *,
        status: str,
        detail: str,
        locked_at,
        locked_by,
        last_error: str | None,
    ) -> None:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT payload_json FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return
            job = JobRecord.model_validate_json(row["payload_json"])
            job.status = status
            job.detail = detail
            job.locked_at = locked_at
            job.locked_by = locked_by
            job.last_error = last_error
            job.updated_at = utc_now()
            connection.execute(
                """
                UPDATE jobs
                SET status = ?, detail = ?, available_at = ?, locked_at = ?, locked_by = ?, last_error = ?, updated_at = ?, payload_json = ?
                WHERE id = ?
                """,
                (
                    job.status,
                    job.detail,
                    job.available_at.isoformat(),
                    job.locked_at.isoformat() if job.locked_at else None,
                    job.locked_by,
                    job.last_error,
                    job.updated_at.isoformat(),
                    job.model_dump_json(),
                    job.id,
                ),
            )
            connection.commit()

    def list_jobs(self, account_id: str | None = None, run_id: str | None = None) -> list[JobRecord]:
        query = """
            SELECT jobs.payload_json
            FROM jobs
            JOIN workflow_runs ON workflow_runs.id = jobs.run_id
        """
        params: list[str] = []
        clauses: list[str] = []
        if account_id:
            clauses.append("workflow_runs.account_id = ?")
            params.append(account_id)
        if run_id:
            clauses.append("jobs.run_id = ?")
            params.append(run_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY datetime(jobs.created_at) DESC, jobs.rowid DESC"
        with closing(self._connect()) as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
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
        jobs = self.list_jobs(run_id=run_id)
        if any(job.status in {"pending", "processing"} for job in jobs):
            run.status = "queued"
        elif any(job.status == "failed" for job in jobs):
            run.status = "degraded"
        else:
            run.status = "completed"
        self.save_run(run)

    def health(self, account_id: str | None = None) -> HealthResponse:
        runs = self.list_runs(account_id)
        completed = sum(1 for run in runs if run.status in {"completed", "degraded"})
        sync_targets = sum(len(run.sync_results) for run in runs)
        return HealthResponse(
            status="healthy",
            database=str(self.database_path),
            total_runs=len(runs),
            completed_runs=completed,
            sync_targets=sync_targets,
        )

    def _deserialize_run(self, payload_json: str) -> WorkflowRun:
        payload = json.loads(payload_json)
        if "ai_analysis" not in payload:
            normalized = NormalizedRecord.model_validate(payload["normalized"])
            payload["ai_analysis"] = WorkflowEngine.build_ai_analysis(normalized, payload["score"]).model_dump()
        return WorkflowRun.model_validate(payload)
