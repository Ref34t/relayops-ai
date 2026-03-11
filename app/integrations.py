from __future__ import annotations

import logging
import time
from uuid import uuid4

import httpx

from app.config import Settings
from app.models import AuditEvent, IntegrationStatus, IntegrationStatusResponse, NormalizedRecord, SyncResult, WorkflowRun
from app.services import WorkflowEngine


class IntegrationManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger("relayops.integrations")

    def status(self) -> IntegrationStatusResponse:
        items = [
            IntegrationStatus(
                provider="OpenAI",
                enabled=bool(self.settings.openai_api_key),
                mode="live" if self.settings.openai_api_key else "disabled",
                detail=f"Responses API via model {self.settings.openai_model}" if self.settings.openai_api_key else "Set OPENAI_API_KEY to enable AI-generated summaries.",
            ),
            IntegrationStatus(
                provider="Slack",
                enabled=bool(self.settings.slack_webhook_url),
                mode="live" if self.settings.slack_webhook_url else "disabled",
                detail="Incoming webhook notifications enabled." if self.settings.slack_webhook_url else "Set SLACK_WEBHOOK_URL to post workflow briefs to Slack.",
            ),
            IntegrationStatus(
                provider="HubSpot",
                enabled=bool(self.settings.hubspot_private_app_token),
                mode="live" if self.settings.hubspot_private_app_token else "disabled",
                detail="CRM contacts sync enabled." if self.settings.hubspot_private_app_token else "Set HUBSPOT_PRIVATE_APP_TOKEN to sync contacts into HubSpot CRM.",
            ),
        ]
        return IntegrationStatusResponse(items=items)

    async def enrich_run(self, run: WorkflowRun) -> WorkflowRun:
        run = await self._apply_openai_summary(run)
        run = await self._apply_hubspot_sync(run)
        run = await self._apply_slack_notification(run)
        return run

    async def _apply_openai_summary(self, run: WorkflowRun) -> WorkflowRun:
        if not self.settings.openai_api_key:
            run.audit_events.append(
                AuditEvent(stage="ai_enrichment", status="skipped", detail="OpenAI integration is not configured.")
            )
            return run

        prompt = (
            "You are generating a concise operations brief for an integrations team. "
            "Summarize the business problem, systems involved, risk level, and next action in 4 sentences max.\n\n"
            f"Company: {run.normalized.company}\n"
            f"Contact: {run.normalized.contact_name}\n"
            f"Urgency: {run.normalized.urgency}\n"
            f"Systems: {', '.join(run.normalized.requested_systems)}\n"
            f"Pain points: {', '.join(run.normalized.pain_points)}\n"
            f"Notes: {run.normalized.notes}\n"
            f"Workflow score: {run.score}/100"
        )

        started = time.perf_counter()
        request_id = str(uuid4())
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/responses",
                    headers={
                        "Authorization": f"Bearer {self.settings.openai_api_key}",
                        "Content-Type": "application/json",
                        "X-Client-Request-Id": request_id,
                    },
                    json={"model": self.settings.openai_model, "input": prompt},
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            self.logger.warning("openai_summary_failed error=%s", exc)
            run.audit_events.append(
                AuditEvent(stage="ai_enrichment", status="failed", detail="OpenAI summary generation failed; deterministic fallback retained.")
            )
            return run

        summary = payload.get("output_text") or self._extract_output_text(payload) or run.summary
        run.summary = summary.strip()
        latency_ms = int((time.perf_counter() - started) * 1000)
        run.audit_events.append(
            AuditEvent(stage="ai_enrichment", status="completed", detail="OpenAI generated the operational brief.")
        )
        self._upsert_sync_result(
            run,
            SyncResult(
                target="OpenAI",
                status="generated",
                detail=f"Summary generated with {self.settings.openai_model}.",
                latency_ms=latency_ms,
                request_id=response.headers.get("x-request-id", request_id),
            ),
        )
        return run

    async def _apply_hubspot_sync(self, run: WorkflowRun) -> WorkflowRun:
        if not self.settings.hubspot_private_app_token:
            run.audit_events.append(
                AuditEvent(stage="hubspot_sync", status="skipped", detail="HubSpot integration is not configured.")
            )
            return run

        started = time.perf_counter()
        headers = {
            "Authorization": f"Bearer {self.settings.hubspot_private_app_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            contact_id = await self._hubspot_lookup_contact(client, headers, run.normalized.email)
            if contact_id:
                endpoint = f"{self.settings.hubspot_base_url}/crm/v3/objects/contacts/{contact_id}"
                method = "PATCH"
            else:
                endpoint = f"{self.settings.hubspot_base_url}/crm/v3/objects/contacts"
                method = "POST"

            payload = {
                "properties": {
                    "email": run.normalized.email,
                    "firstname": run.normalized.contact_name.split(" ")[0],
                    "lastname": " ".join(run.normalized.contact_name.split(" ")[1:]) or run.normalized.contact_name.split(" ")[0],
                    "company": run.normalized.company,
                    "jobtitle": "Operational stakeholder",
                }
            }

            try:
                response = await client.request(method, endpoint, headers=headers, json=payload)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                self.logger.warning("hubspot_sync_failed error=%s", exc)
                run.audit_events.append(
                    AuditEvent(stage="hubspot_sync", status="failed", detail="HubSpot contact sync failed.")
                )
                self._upsert_sync_result(
                    run,
                    SyncResult(
                        target="HubSpot",
                        status="failed",
                        detail="HubSpot contact sync failed.",
                        latency_ms=int((time.perf_counter() - started) * 1000),
                    ),
                )
                return run

        latency_ms = int((time.perf_counter() - started) * 1000)
        run.audit_events.append(
            AuditEvent(stage="hubspot_sync", status="completed", detail="HubSpot contact sync completed.")
        )
        self._upsert_sync_result(
            run,
            SyncResult(
                target="HubSpot",
                status="synced",
                detail="Contact created or updated in HubSpot CRM.",
                latency_ms=latency_ms,
                request_id=response.headers.get("x-hubspot-correlation-id"),
            ),
        )
        return run

    async def _hubspot_lookup_contact(self, client: httpx.AsyncClient, headers: dict[str, str], email: str) -> str | None:
        response = await client.post(
            f"{self.settings.hubspot_base_url}/crm/v3/objects/contacts/batch/read",
            headers=headers,
            json={"idProperty": "email", "properties": ["email"], "inputs": [{"id": email}]},
        )
        if response.status_code >= 400:
            return None
        payload = response.json()
        results = payload.get("results", [])
        if not results:
            return None
        return results[0].get("id")

    async def _apply_slack_notification(self, run: WorkflowRun) -> WorkflowRun:
        if not self.settings.slack_webhook_url:
            run.audit_events.append(
                AuditEvent(stage="slack_notify", status="skipped", detail="Slack integration is not configured.")
            )
            return run

        started = time.perf_counter()
        payload = {
            "text": f"RelayOps workflow for {run.normalized.company} scored {run.score}/100.",
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*RelayOps workflow:* {run.normalized.company}"},
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Urgency*\n{run.normalized.urgency}"},
                        {"type": "mrkdwn", "text": f"*Score*\n{run.score}/100"},
                        {"type": "mrkdwn", "text": f"*Systems*\n{', '.join(run.normalized.requested_systems)}"},
                        {"type": "mrkdwn", "text": f"*Source*\n{run.source}"},
                    ],
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": run.summary},
                },
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(self.settings.slack_webhook_url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            self.logger.warning("slack_notify_failed error=%s", exc)
            run.audit_events.append(
                AuditEvent(stage="slack_notify", status="failed", detail="Slack notification failed.")
            )
            self._upsert_sync_result(
                run,
                SyncResult(
                    target="Slack",
                    status="failed",
                    detail="Slack notification failed.",
                    latency_ms=int((time.perf_counter() - started) * 1000),
                ),
            )
            return run

        latency_ms = int((time.perf_counter() - started) * 1000)
        run.audit_events.append(
            AuditEvent(stage="slack_notify", status="completed", detail="Slack incoming webhook delivered the workflow brief.")
        )
        self._upsert_sync_result(
            run,
            SyncResult(
                target="Slack",
                status="notified",
                detail="Workflow brief posted to Slack.",
                latency_ms=latency_ms,
                request_id=response.headers.get("x-slack-req-id"),
            ),
        )
        return run

    @staticmethod
    def _extract_output_text(payload: dict) -> str:
        output_chunks = payload.get("output", [])
        texts: list[str] = []
        for item in output_chunks:
            for content in item.get("content", []):
                text = content.get("text")
                if text:
                    texts.append(text)
        return "\n".join(texts).strip()

    @staticmethod
    def _upsert_sync_result(run: WorkflowRun, result: SyncResult) -> None:
        for index, existing in enumerate(run.sync_results):
            if existing.target == result.target:
                run.sync_results[index] = result
                return
        run.sync_results.append(result)
