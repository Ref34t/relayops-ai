from __future__ import annotations

import logging
from uuid import uuid4

from app.models import AuditEvent, IntakePayload, NormalizedRecord, SyncResult, WorkflowAction, WorkflowRequest, WorkflowRun


class DataNormalizer:
    FIELD_ALIASES = {
        "company": ["company", "company_name", "org", "organization"],
        "contact_name": ["contact_name", "name", "contact", "full_name"],
        "email": ["email", "email_address", "work_email"],
        "pain_points": ["pain_points", "challenges", "issues", "painPoints"],
        "requested_systems": ["requested_systems", "systems", "tools", "requestedTools"],
        "monthly_revenue": ["monthly_revenue", "mrr", "revenue_band"],
        "urgency": ["urgency", "priority", "timeline"],
        "notes": ["notes", "context", "brief"],
    }

    @classmethod
    def normalize(cls, intake: IntakePayload) -> NormalizedRecord:
        payload = intake.payload
        normalized: dict[str, object] = {}

        for target, aliases in cls.FIELD_ALIASES.items():
            normalized[target] = next(
                (payload[key] for key in aliases if key in payload and payload[key]),
                "" if target in {"monthly_revenue", "notes"} else [],
            )

        return NormalizedRecord(
            company=str(normalized["company"] or "Unknown account").strip(),
            contact_name=str(normalized["contact_name"] or "Unassigned contact").strip(),
            email=str(normalized["email"] or "missing@example.com").strip().lower(),
            pain_points=cls._coerce_list(normalized["pain_points"]) or ["Fragmented data"],
            requested_systems=cls._coerce_list(normalized["requested_systems"]) or ["CRM"],
            monthly_revenue=str(normalized["monthly_revenue"] or "Undisclosed").strip(),
            urgency=cls._normalize_urgency(str(normalized["urgency"] or "medium")),
            source=intake.source,
            notes=str(normalized["notes"] or "No additional notes supplied.").strip(),
        )

    @staticmethod
    def from_request(request: WorkflowRequest) -> NormalizedRecord:
        return NormalizedRecord(
            company=request.company,
            contact_name=request.contact_name,
            email=request.email.lower(),
            pain_points=request.pain_points,
            requested_systems=request.requested_systems,
            monthly_revenue=request.monthly_revenue,
            urgency=DataNormalizer._normalize_urgency(request.urgency),
            source=request.source,
            notes=request.notes or "No additional notes supplied.",
        )

    @staticmethod
    def _coerce_list(value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [part.strip() for part in value.split(",") if part.strip()]
        return []

    @staticmethod
    def _normalize_urgency(value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned in {"critical", "urgent", "high"}:
            return "high"
        if cleaned in {"low", "later"}:
            return "low"
        return "medium"


class WorkflowEngine:
    logger = logging.getLogger("relayops.workflow")

    @staticmethod
    def score(record: NormalizedRecord) -> int:
        score = 50
        score += 20 if record.urgency == "high" else 0
        score += 10 if len(record.requested_systems) > 2 else 0
        score += 8 if "manual reporting" in " ".join(record.pain_points).lower() else 0
        score += 7 if "hubspot" in " ".join(record.requested_systems).lower() else 0
        return min(score, 99)

    @classmethod
    def build_actions(cls, record: NormalizedRecord, score: int) -> list[WorkflowAction]:
        priority = "high" if score >= 75 else "medium"
        systems = ", ".join(record.requested_systems[:3])

        return [
            WorkflowAction(
                label=f"Normalize inbound data for {record.company}",
                owner="Integration Layer",
                system="Webhook Gateway",
                priority=priority,
            ),
            WorkflowAction(
                label=f"Sync record into {systems}",
                owner="Ops Automation",
                system="CRM + Finance",
                priority=priority,
            ),
            WorkflowAction(
                label="Generate stakeholder brief and handoff",
                owner="AI Copilot",
                system="LLM Summary Service",
                priority="medium",
            ),
        ]

    @staticmethod
    def summarize(record: NormalizedRecord, score: int) -> str:
        systems = ", ".join(record.requested_systems)
        problems = ", ".join(record.pain_points[:3])
        return (
            f"{record.company} needs an AI-assisted integration workflow across {systems}. "
            f"The main blockers are {problems}. "
            f"Current urgency is {record.urgency}, so the recommended approach is a monitored async pipeline "
            f"that cleans inbound records, pushes updates to client systems, and produces concise decision briefs. "
            f"Workflow confidence score: {score}/100."
        )

    @staticmethod
    def build_audit_events(record: NormalizedRecord, score: int) -> list[AuditEvent]:
        return [
            AuditEvent(stage="ingest", status="completed", detail=f"Accepted payload from {record.source}."),
            AuditEvent(stage="normalize", status="completed", detail=f"Standardized fields for {record.company}."),
            AuditEvent(stage="score", status="completed", detail=f"Assigned workflow score {score}/100."),
            AuditEvent(stage="brief", status="completed", detail="Prepared stakeholder-ready operational brief."),
            AuditEvent(stage="sync", status="completed", detail="Queued downstream system updates."),
        ]

    @staticmethod
    def build_sync_results(record: NormalizedRecord) -> list[SyncResult]:
        sync_targets: list[SyncResult] = []
        for index, system in enumerate(record.requested_systems[:3], start=1):
            sync_targets.append(
                SyncResult(
                    target=system,
                    status="planned",
                    detail=f"Prepared normalized payload for {system}; live connector pending.",
                    latency_ms=110 + index * 35,
                )
            )
        sync_targets.append(
            SyncResult(
                target="Slack",
                status="planned",
                detail="Prepared operational brief notification; live delivery pending.",
                latency_ms=95,
            )
        )
        return sync_targets

    @classmethod
    def run(cls, record: NormalizedRecord) -> WorkflowRun:
        score = cls.score(record)
        cls.logger.info("workflow_run company=%s source=%s score=%s", record.company, record.source, score)
        return WorkflowRun(
            id=str(uuid4())[:8],
            source=record.source,
            normalized=record,
            score=score,
            summary=cls.summarize(record, score),
            actions=cls.build_actions(record, score),
            audit_events=cls.build_audit_events(record, score),
            sync_results=cls.build_sync_results(record),
            status="completed",
        )


def seed_requests() -> list[WorkflowRequest]:
    return [
            WorkflowRequest(
                source="hubspot",
                company="Nile Freight Group",
                contact_name="Mariam Hassan",
                email="mariam@nilefreight.co",
                pain_points=["Manual reporting", "Disconnected CRM and finance data", "Slow approvals"],
                requested_systems=["HubSpot", "Xero", "Slack"],
                monthly_revenue="€120k-€180k",
                urgency="high",
                notes="Regional team wants fewer handoffs and clearer weekly visibility.",
            ),
            WorkflowRequest(
                source="typeform",
                company="Cedar Clinics",
                contact_name="Omar Adel",
                email="omar@cedarclinics.com",
                pain_points=["Repetitive lead qualification", "No central patient inquiry log"],
                requested_systems=["Salesforce", "Google Sheets"],
                monthly_revenue="€60k-€90k",
                urgency="medium",
                notes="Needs a fast proof-of-concept before rollout to multiple branches.",
            ),
        ]
