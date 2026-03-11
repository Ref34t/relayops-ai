from __future__ import annotations

import logging
import time
from uuid import uuid4

import httpx

from app.config import Settings
from app.models import (
    AuditEvent,
    IntegrationCheckResponse,
    IntegrationSecretPreview,
    IntegrationStatus,
    IntegrationStatusResponse,
    RuntimeSettingsResponse,
    SyncResult,
    WorkflowRun,
)


class IntegrationManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = logging.getLogger("relayops.integrations")
        self.provider_diagnostics: dict[str, tuple[str, str]] = {}

    def status(self) -> IntegrationStatusResponse:
        items = [
            IntegrationStatus(
                provider="OpenAI",
                enabled=bool(self.settings.openai_api_key),
                mode=self._provider_mode("OpenAI", "ready" if self.settings.openai_api_key else "disabled"),
                detail=self._provider_detail(
                    "OpenAI",
                    f"Responses API via model {self.settings.openai_model}" if self.settings.openai_api_key else "Set OPENAI_API_KEY to enable AI-generated summaries.",
                ),
                action="Add OPENAI_API_KEY to enable live summaries." if not self.settings.openai_api_key else "Run a workflow or connector check to verify the configured model.",
            ),
            IntegrationStatus(
                provider="Slack",
                enabled=bool(self.settings.slack_webhook_url),
                mode=self._provider_mode("Slack", "ready" if self.settings.slack_webhook_url else "disabled"),
                detail=self._provider_detail(
                    "Slack",
                    "Incoming webhook notifications enabled." if self.settings.slack_webhook_url else "Set SLACK_WEBHOOK_URL to post workflow briefs to Slack.",
                ),
                action="Use an incoming webhook URL for a dedicated channel." if not self.settings.slack_webhook_url else "Trigger a workflow to verify delivery.",
            ),
            IntegrationStatus(
                provider="HubSpot",
                enabled=bool(self.settings.hubspot_private_app_token),
                mode=self._provider_mode("HubSpot", "ready" if self.settings.hubspot_private_app_token else "disabled"),
                detail=self._provider_detail(
                    "HubSpot",
                    "CRM contacts sync enabled." if self.settings.hubspot_private_app_token else "Set HUBSPOT_PRIVATE_APP_TOKEN to sync contacts into HubSpot CRM.",
                ),
                action="Grant CRM contact scopes to the private app token." if self.settings.hubspot_private_app_token else "Add HUBSPOT_PRIVATE_APP_TOKEN with CRM scopes.",
            ),
        ]
        return IntegrationStatusResponse(items=items)

    def runtime_settings(self) -> RuntimeSettingsResponse:
        return RuntimeSettingsResponse(
            items=[
                IntegrationSecretPreview(
                    provider="OpenAI",
                    env_var="OPENAI_API_KEY",
                    configured=bool(self.settings.openai_api_key),
                    preview=self._mask_secret(self.settings.openai_api_key),
                    source=".env or process environment",
                ),
                IntegrationSecretPreview(
                    provider="OpenAI Model",
                    env_var="OPENAI_MODEL",
                    configured=bool(self.settings.openai_model),
                    preview=self.settings.openai_model,
                    source=".env or process environment",
                ),
                IntegrationSecretPreview(
                    provider="Slack",
                    env_var="SLACK_WEBHOOK_URL",
                    configured=bool(self.settings.slack_webhook_url),
                    preview=self._mask_url(self.settings.slack_webhook_url),
                    source=".env or process environment",
                ),
                IntegrationSecretPreview(
                    provider="HubSpot",
                    env_var="HUBSPOT_PRIVATE_APP_TOKEN",
                    configured=bool(self.settings.hubspot_private_app_token),
                    preview=self._mask_secret(self.settings.hubspot_private_app_token),
                    source=".env or process environment",
                ),
                IntegrationSecretPreview(
                    provider="HubSpot Base URL",
                    env_var="HUBSPOT_BASE_URL",
                    configured=bool(self.settings.hubspot_base_url),
                    preview=self.settings.hubspot_base_url,
                    source=".env or process environment",
                ),
            ]
        )

    async def check_integrations(self) -> IntegrationCheckResponse:
        return IntegrationCheckResponse(
            items=[
                await self._check_openai_status(),
                self._check_slack_status(),
                await self._check_hubspot_status(),
            ]
        )

    async def enrich_run(self, run: WorkflowRun) -> WorkflowRun:
        run = await self._apply_openai_summary(run)
        run = await self._apply_hubspot_sync(run)
        run = await self._apply_slack_notification(run)
        return run

    async def process_provider(self, provider: str, run: WorkflowRun) -> WorkflowRun:
        handlers = {
            "openai": self._apply_openai_summary,
            "hubspot": self._apply_hubspot_sync,
            "slack": self._apply_slack_notification,
        }
        handler = handlers.get(provider)
        if not handler:
            return run
        return await handler(run)

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
            self.provider_diagnostics["OpenAI"] = ("failed", "OpenAI summary generation failed; deterministic fallback retained.")
            run.audit_events.append(
                AuditEvent(stage="ai_enrichment", status="failed", detail="OpenAI summary generation failed; deterministic fallback retained.")
            )
            return run

        summary = payload.get("output_text") or self._extract_output_text(payload) or run.summary
        run.summary = summary.strip()
        run.ai_analysis.highlights = [
            "AI-generated brief replaced the deterministic summary for this run.",
            *run.ai_analysis.highlights[:2],
        ]
        latency_ms = int((time.perf_counter() - started) * 1000)
        run.audit_events.append(
            AuditEvent(stage="ai_enrichment", status="completed", detail="OpenAI generated the operational brief.")
        )
        self.provider_diagnostics["OpenAI"] = ("live", f"OpenAI summary generated with {self.settings.openai_model}.")
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
            self.provider_diagnostics["HubSpot"] = ("disabled", "HubSpot integration is not configured.")
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
                self.provider_diagnostics["HubSpot"] = self._hubspot_error_state(exc)
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
        self.provider_diagnostics["HubSpot"] = ("live", "HubSpot contact create/update succeeded.")
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
            self.provider_diagnostics["Slack"] = ("disabled", "Slack integration is not configured.")
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
            self.provider_diagnostics["Slack"] = ("failed", "Slack notification failed.")
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
        self.provider_diagnostics["Slack"] = ("live", "Slack incoming webhook delivered successfully.")
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

    def _provider_mode(self, provider: str, fallback: str) -> str:
        return self.provider_diagnostics.get(provider, (fallback, ""))[0]

    def _provider_detail(self, provider: str, fallback: str) -> str:
        return self.provider_diagnostics.get(provider, ("", fallback))[1] or fallback

    @staticmethod
    def _mask_secret(value: str | None) -> str:
        if not value:
            return "Not loaded"
        if len(value) <= 10:
            return "*" * len(value)
        return f"{value[:6]}...{value[-4:]}"

    @staticmethod
    def _mask_url(value: str | None) -> str:
        if not value:
            return "Not loaded"
        if len(value) <= 24:
            return IntegrationManager._mask_secret(value)
        return f"{value[:24]}...{value[-8:]}"

    async def _check_openai_status(self) -> IntegrationStatus:
        if not self.settings.openai_api_key:
            return IntegrationStatus(
                provider="OpenAI",
                enabled=False,
                mode="disabled",
                detail="Set OPENAI_API_KEY to enable AI-generated summaries.",
                action="Add OPENAI_API_KEY to enable live summaries.",
            )

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"https://api.openai.com/v1/models/{self.settings.openai_model}",
                    headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                )
                response.raise_for_status()
        except httpx.HTTPError:
            self.provider_diagnostics["OpenAI"] = ("misconfigured", f"OpenAI model check failed for {self.settings.openai_model}.")
        else:
            self.provider_diagnostics["OpenAI"] = ("ready", f"OpenAI model {self.settings.openai_model} is reachable.")

        return self.status().items[0]

    def _check_slack_status(self) -> IntegrationStatus:
        if not self.settings.slack_webhook_url:
            return IntegrationStatus(
                provider="Slack",
                enabled=False,
                mode="disabled",
                detail="Set SLACK_WEBHOOK_URL to post workflow briefs to Slack.",
                action="Use an incoming webhook URL for a dedicated channel.",
            )

        if self.settings.slack_webhook_url.startswith("https://hooks.slack.com/services/"):
            self.provider_diagnostics["Slack"] = ("ready", "Slack webhook format looks valid. Trigger a workflow to verify delivery.")
        else:
            self.provider_diagnostics["Slack"] = ("misconfigured", "Slack webhook format does not look valid.")
        return self.status().items[1]

    async def _check_hubspot_status(self) -> IntegrationStatus:
        if not self.settings.hubspot_private_app_token:
            return IntegrationStatus(
                provider="HubSpot",
                enabled=False,
                mode="disabled",
                detail="Set HUBSPOT_PRIVATE_APP_TOKEN to sync contacts into HubSpot CRM.",
                action="Add HUBSPOT_PRIVATE_APP_TOKEN with CRM scopes.",
            )

        headers = {"Authorization": f"Bearer {self.settings.hubspot_private_app_token}"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.settings.hubspot_base_url}/crm/v3/objects/contacts",
                    headers=headers,
                    params={"limit": 1},
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            self.provider_diagnostics["HubSpot"] = self._hubspot_error_state(exc)
        else:
            self.provider_diagnostics["HubSpot"] = ("ready", "HubSpot token is reachable and contact scope is valid.")

        return self.status().items[2]

    @staticmethod
    def _hubspot_error_state(exc: httpx.HTTPError) -> tuple[str, str]:
        response = getattr(exc, "response", None)
        if response is None:
            return "failed", "HubSpot request failed before a response was received."
        if response.status_code == 401:
            return "misconfigured", "HubSpot token was rejected with 401 Unauthorized."
        if response.status_code == 403:
            return "misconfigured", "HubSpot token is missing required CRM scopes."
        return "failed", f"HubSpot request failed with status {response.status_code}."
