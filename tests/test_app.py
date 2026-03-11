from __future__ import annotations

import os
import tempfile
import unittest
import sqlite3
import json

import httpx

from app.main import create_app
from app.models import WorkflowRun
from app.config import get_settings
from app.integrations import IntegrationManager
from app.jobs import JobRunner


class RelayOpsAppTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["RELAYOPS_DB_PATH"] = f"{self.temp_dir.name}/test.db"
        os.environ["RELAYOPS_TRACE_EXPORTER"] = "disabled"
        self.app = create_app()
        self.repository = self.app.state.repository

    def tearDown(self) -> None:
        os.environ.pop("RELAYOPS_DB_PATH", None)
        os.environ.pop("RELAYOPS_TRACE_EXPORTER", None)
        os.environ.pop("RELAYOPS_RUN_JOBS_IN_WEB", None)
        os.environ.pop("RELAYOPS_RATE_LIMIT_PER_MINUTE", None)
        self.temp_dir.cleanup()

    async def test_overview_exposes_seeded_runs(self) -> None:
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/overview")

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["title"], "RelayOps AI")
        self.assertGreaterEqual(len(payload["recent_runs"]), 2)
        self.assertTrue(payload["capabilities"])

    async def test_execute_workflow_creates_run(self) -> None:
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/workflows/execute",
                json={
                    "source": "hubspot",
                    "company": "Atlas Retail Ops",
                    "contact_name": "Laila Fathy",
                    "email": "laila@atlasretail.ai",
                    "pain_points": ["Manual reporting", "Slow approvals"],
                    "requested_systems": ["HubSpot", "NetSuite", "Slack"],
                    "monthly_revenue": "EUR 90k-140k",
                    "urgency": "high",
                    "notes": "Leadership needs a weekly summary.",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["normalized"]["company"], "Atlas Retail Ops")
        self.assertEqual(payload["normalized"]["urgency"], "high")
        self.assertEqual(payload["status"], "queued")
        self.assertGreaterEqual(payload["score"], 70)
        self.assertTrue(payload["audit_events"])
        self.assertTrue(payload["sync_results"])

    async def test_webhook_intake_normalizes_alias_fields(self) -> None:
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/webhooks/intake",
                json={
                    "source": "typeform",
                    "payload": {
                        "company_name": "Cairo Service Desk",
                        "full_name": "Nour Tarek",
                        "work_email": "NOUR@EXAMPLE.COM",
                        "issues": "Manual reporting, missing visibility",
                        "requestedTools": ["HubSpot", "Slack"],
                        "priority": "urgent",
                        "brief": "Needs better routing.",
                    },
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["normalized"]["company"], "Cairo Service Desk")
        self.assertEqual(payload["normalized"]["contact_name"], "Nour Tarek")
        self.assertEqual(payload["normalized"]["email"], "nour@example.com")
        self.assertEqual(payload["normalized"]["urgency"], "high")
        self.assertEqual(payload["normalized"]["requested_systems"], ["HubSpot", "Slack"])
        self.assertIn("Manual reporting", payload["summary"])

    async def test_health_reports_persisted_state(self) -> None:
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["status"], "healthy")
        self.assertGreaterEqual(payload["total_runs"], 2)
        self.assertGreaterEqual(payload["sync_targets"], 1)

    async def test_integrations_report_disabled_without_env(self) -> None:
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/integrations")

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(len(payload["items"]), 3)
        self.assertTrue(all(item["enabled"] is False for item in payload["items"]))

    async def test_integration_check_reports_disabled_without_env(self) -> None:
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/integrations/check")

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(len(payload["items"]), 3)
        self.assertTrue(all(item["mode"] == "disabled" for item in payload["items"]))

    async def test_account_endpoint_returns_demo_account(self) -> None:
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/account")

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["account"]["email"], "demo@relayops.app")
        self.assertTrue(payload["account"]["api_key"])
        self.assertEqual(payload["auth_mode"], "demo")

    async def test_login_creates_session(self) -> None:
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/auth/login",
                json={"email": "demo@relayops.app", "password": "relayops-demo-pass"},
            )
            account = await client.get("/api/account")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(account.status_code, 200)
        self.assertEqual(account.json()["auth_mode"], "session")

    async def test_register_creates_account_and_session(self) -> None:
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/auth/register",
                json={"name": "Northstar Ops", "email": "ops@northstar.ai", "password": "northstar-secret"},
            )
            account = await client.get("/api/account")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["account"]["email"], "ops@northstar.ai")
        self.assertEqual(account.json()["account"]["email"], "ops@northstar.ai")

    async def test_logout_clears_session_and_returns_to_demo(self) -> None:
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/auth/register",
                json={"name": "Northstar Ops", "email": "ops@northstar.ai", "password": "northstar-secret"},
            )
            before_logout = await client.get("/api/account")
            logout = await client.post("/api/auth/logout")
            after_logout = await client.get("/api/account")

        self.assertEqual(before_logout.status_code, 200)
        self.assertEqual(before_logout.json()["auth_mode"], "session")
        self.assertEqual(logout.status_code, 200)
        self.assertEqual(after_logout.status_code, 200)
        self.assertEqual(after_logout.json()["auth_mode"], "demo")
        self.assertEqual(after_logout.json()["account"]["email"], "demo@relayops.app")

    async def test_jobs_endpoint_exposes_queue_records(self) -> None:
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/workflows/execute",
                json={
                    "source": "hubspot",
                    "company": "Queue Example",
                    "contact_name": "Queue User",
                    "email": "queue@example.com",
                    "pain_points": ["Manual routing"],
                    "requested_systems": ["HubSpot"],
                    "monthly_revenue": "EUR 50k-70k",
                    "urgency": "medium",
                    "notes": "Queue verification.",
                },
            )
            response = await client.get("/api/jobs")

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertGreaterEqual(len(payload), 3)

    async def test_invalid_api_key_is_rejected(self) -> None:
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/account", headers={"X-RelayOps-Api-Key": "bad-key"})

        self.assertEqual(response.status_code, 401)

    async def test_metrics_endpoint_exposes_prometheus_output(self) -> None:
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/metrics")

        self.assertEqual(response.status_code, 200)
        self.assertIn("relayops_http_requests_total", response.text)

    async def test_rate_limit_returns_429(self) -> None:
        os.environ["RELAYOPS_RATE_LIMIT_PER_MINUTE"] = "1"
        app = create_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = await client.get("/api/health", headers={"X-RelayOps-Api-Key": "relayops-demo-key"})
            second = await client.get("/api/health", headers={"X-RelayOps-Api-Key": "relayops-demo-key"})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)

    async def test_overview_is_scoped_to_current_account(self) -> None:
        other = self.repository.create_account("Other Workspace", "other@relayops.app", "other-key")
        seeded = self.repository.list_runs(self.repository.get_default_account().id)
        run = WorkflowRun.model_validate(seeded[0].model_dump())
        run.id = "otherrun1"
        run.account_id = other.id
        run.normalized.company = "Other Tenant Co"
        self.repository.save_run(run)

        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/overview", headers={"X-RelayOps-Api-Key": "other-key"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["recent_runs"]), 1)
        self.assertEqual(payload["recent_runs"][0]["normalized"]["company"], "Other Tenant Co")

    async def test_jobs_are_scoped_to_current_account(self) -> None:
        other = self.repository.create_account("Queue Workspace", "queue@relayops.app", "queue-key")
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post(
                "/api/workflows/execute",
                headers={"X-RelayOps-Api-Key": "queue-key"},
                json={
                    "source": "hubspot",
                    "company": "Queue Scoped",
                    "contact_name": "Scoped User",
                    "email": "scoped@example.com",
                    "pain_points": ["Manual routing"],
                    "requested_systems": ["HubSpot"],
                    "monthly_revenue": "EUR 50k-70k",
                    "urgency": "medium",
                    "notes": "Queue scope verification.",
                },
            )
            response = await client.get("/api/jobs", headers={"X-RelayOps-Api-Key": "queue-key"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload)
        run_ids = {job["run_id"] for job in payload}
        for run_id in run_ids:
            stored = self.repository.get_run(run_id)
            self.assertEqual(stored.account_id, other.id)

    async def test_legacy_database_payload_is_upgraded_on_read(self) -> None:
        legacy_dir = tempfile.TemporaryDirectory()
        legacy_db = f"{legacy_dir.name}/legacy.db"
        connection = sqlite3.connect(legacy_db)
        connection.execute(
            """
            CREATE TABLE workflow_runs (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                score INTEGER NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        payload = {
            "id": "legacy1",
            "created_at": "2026-03-11T10:00:00Z",
            "source": "hubspot",
            "normalized": {
                "company": "Legacy Co",
                "contact_name": "Legacy User",
                "email": "legacy@example.com",
                "pain_points": ["Manual reporting"],
                "requested_systems": ["HubSpot"],
                "monthly_revenue": "EUR 40k-50k",
                "urgency": "high",
                "source": "hubspot",
                "notes": "Legacy payload",
            },
            "score": 88,
            "summary": "Legacy summary",
            "actions": [],
            "audit_events": [],
            "sync_results": [],
            "status": "completed",
        }
        connection.execute(
            "INSERT INTO workflow_runs (id, created_at, source, status, score, payload_json) VALUES (?, ?, ?, ?, ?, ?)",
            ("legacy1", "2026-03-11T10:00:00Z", "hubspot", "completed", 88, json.dumps(payload)),
        )
        connection.commit()
        connection.close()

        os.environ["RELAYOPS_DB_PATH"] = legacy_db
        legacy_app = create_app()
        legacy_runs = legacy_app.state.repository.list_runs()
        self.assertEqual(legacy_runs[0].normalized.company, "Legacy Co")
        self.assertTrue(legacy_runs[0].ai_analysis.highlights)
        with sqlite3.connect(legacy_db) as migrated:
            job_columns = {row[1] for row in migrated.execute("PRAGMA table_info(jobs)").fetchall()}
            account_columns = {row[1] for row in migrated.execute("PRAGMA table_info(accounts)").fetchall()}
        self.assertIn("max_attempts", job_columns)
        self.assertIn("password_hash", account_columns)
        legacy_dir.cleanup()

    async def test_worker_processes_jobs_when_web_mode_disabled(self) -> None:
        os.environ["RELAYOPS_RUN_JOBS_IN_WEB"] = "0"
        app = create_app()
        repository = app.state.repository
        settings = get_settings()
        runner = JobRunner(repository, IntegrationManager(settings), poll_interval_ms=10)

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/workflows/execute",
                json={
                    "source": "hubspot",
                    "company": "Worker Example",
                    "contact_name": "Worker User",
                    "email": "worker@example.com",
                    "pain_points": ["Manual routing"],
                    "requested_systems": ["HubSpot"],
                    "monthly_revenue": "EUR 50k-70k",
                    "urgency": "medium",
                    "notes": "Worker verification.",
                },
            )

        run_id = response.json()["id"]
        await runner.process_pending_jobs(run_id)
        run = repository.get_run(run_id)
        self.assertIn(run.status, {"completed", "degraded"})


if __name__ == "__main__":
    unittest.main()
