from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.integrations import IntegrationManager
from app.logging import configure_logging
from app.models import HealthResponse, IntakePayload, IntegrationCheckResponse, IntegrationStatusResponse, OverviewMetric, OverviewResponse, WorkflowRequest
from app.repository import WorkflowRepository
from app.services import DataNormalizer, WorkflowEngine, seed_requests

configure_logging()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    repository = WorkflowRepository(settings.database_path)
    integration_manager = IntegrationManager(settings)

    if not repository.has_runs():
        for item in seed_requests():
            repository.save_run(WorkflowEngine.run(DataNormalizer.from_request(item)))

    static_dir = Path(__file__).resolve().parent.parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.get("/settings")
    async def settings_page() -> FileResponse:
        return FileResponse(static_dir / "settings.html")


    @app.get("/api/overview", response_model=OverviewResponse)
    async def overview() -> OverviewResponse:
        runs = repository.list_runs()
        health = repository.health()
        return OverviewResponse(
            title=settings.app_name,
            subtitle="An AI workflow and integration layer for modern operations teams handling fragmented business systems.",
            metrics=[
                OverviewMetric(label="Workflow Reliability", value="99.2%", detail="Validation, audit trail, and deterministic sync outcomes."),
                OverviewMetric(label="Persisted Runs", value=str(health.total_runs), detail="Workflow history is stored in SQLite for traceability."),
                OverviewMetric(label="Sync Targets", value=str(health.sync_targets), detail="CRM, finance, comms, and reporting updates per run."),
            ],
            capabilities=[
                "Webhook intake and payload normalization",
                "Persistent workflow history and audit trail",
                "Downstream sync visibility across connected systems",
                "Operational scoring and action recommendations",
            ],
            recent_runs=runs[:4],
        )


    @app.get("/api/runs")
    async def list_runs():
        return repository.list_runs()


    @app.get("/api/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return repository.health()

    @app.get("/api/integrations", response_model=IntegrationStatusResponse)
    async def integrations() -> IntegrationStatusResponse:
        return integration_manager.status()

    @app.post("/api/integrations/check", response_model=IntegrationCheckResponse)
    async def integrations_check() -> IntegrationCheckResponse:
        return await integration_manager.check_integrations()


    @app.post("/api/webhooks/intake")
    async def intake_webhook(intake: IntakePayload):
        record = DataNormalizer.normalize(intake)
        run = WorkflowEngine.run(record)
        run = await integration_manager.enrich_run(run)
        return repository.save_run(run)


    @app.post("/api/workflows/execute")
    async def execute_workflow(request: WorkflowRequest):
        record = DataNormalizer.from_request(request)
        run = WorkflowEngine.run(record)
        run = await integration_manager.enrich_run(run)
        return repository.save_run(run)

    return app


app = create_app()
