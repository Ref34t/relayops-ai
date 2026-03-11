from __future__ import annotations

import os
import tempfile
import unittest

import httpx

from app.main import create_app


class RelayOpsAppTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["RELAYOPS_DB_PATH"] = f"{self.temp_dir.name}/test.db"
        self.app = create_app()

    def tearDown(self) -> None:
        os.environ.pop("RELAYOPS_DB_PATH", None)
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
        self.assertEqual(payload["status"], "completed")
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


if __name__ == "__main__":
    unittest.main()
