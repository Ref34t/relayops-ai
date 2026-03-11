from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IntakePayload(BaseModel):
    source: str = Field(..., examples=["hubspot"])
    payload: dict[str, Any]


class NormalizedRecord(BaseModel):
    company: str
    contact_name: str
    email: str
    pain_points: list[str]
    requested_systems: list[str]
    monthly_revenue: str
    urgency: str
    source: str
    notes: str


class WorkflowAction(BaseModel):
    label: str
    owner: str
    system: str
    priority: str


class AuditEvent(BaseModel):
    timestamp: datetime = Field(default_factory=utc_now)
    stage: str
    status: str
    detail: str


class SyncResult(BaseModel):
    target: str
    status: str
    detail: str
    latency_ms: int
    request_id: str | None = None


class AIAnalysis(BaseModel):
    risk_level: str
    executive_title: str
    highlights: list[str]
    next_steps: list[str]
    automation_opportunities: list[str]


class WorkflowRun(BaseModel):
    id: str
    created_at: datetime = Field(default_factory=utc_now)
    account_id: str | None = None
    source: str
    normalized: NormalizedRecord
    score: int
    summary: str
    ai_analysis: AIAnalysis
    actions: list[WorkflowAction]
    audit_events: list[AuditEvent]
    sync_results: list[SyncResult]
    status: str


class WorkflowRequest(BaseModel):
    source: str
    company: str
    contact_name: str
    email: str
    pain_points: list[str]
    requested_systems: list[str]
    monthly_revenue: str
    urgency: str
    notes: str = ""


class Account(BaseModel):
    id: str
    name: str
    email: str
    api_key: str
    created_at: datetime = Field(default_factory=utc_now)


class JobRecord(BaseModel):
    id: str
    run_id: str
    provider: str
    status: str
    detail: str
    attempts: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class OverviewMetric(BaseModel):
    label: str
    value: str
    detail: str


class OverviewResponse(BaseModel):
    title: str
    subtitle: str
    metrics: list[OverviewMetric]
    capabilities: list[str]
    recent_runs: list[WorkflowRun]


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime = Field(default_factory=utc_now)
    database: str
    total_runs: int
    completed_runs: int
    sync_targets: int


class IntegrationStatus(BaseModel):
    provider: str
    enabled: bool
    mode: str
    detail: str
    action: str | None = None


class IntegrationStatusResponse(BaseModel):
    items: list[IntegrationStatus]


class IntegrationCheckResponse(BaseModel):
    items: list[IntegrationStatus]


class AccountResponse(BaseModel):
    account: Account
