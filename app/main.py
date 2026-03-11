from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.auth import get_current_account, session_expiry, verify_password
from app.config import get_settings
from app.integrations import IntegrationManager
from app.jobs import JobRunner
from app.logging import configure_logging
from app.models import (
    AccountResponse,
    AuthResponse,
    HealthResponse,
    IntakePayload,
    IntegrationCheckResponse,
    RuntimeSettingsResponse,
    IntegrationStatusResponse,
    LoginRequest,
    OverviewMetric,
    OverviewResponse,
    RegisterRequest,
    WorkflowRequest,
)
from app.observability import (
    SlidingWindowRateLimiter,
    capture_exception,
    get_tracer,
    metrics_response,
    new_trace_context,
    observe_request,
    setup_observability,
)
from app.repository import WorkflowRepository
from app.services import DataNormalizer, WorkflowEngine, seed_requests


@asynccontextmanager
async def lifespan(app: FastAPI):
    repository = app.state.repository
    job_runner = app.state.job_runner
    settings = app.state.settings
    repository.purge_expired_sessions()
    if settings.run_jobs_in_web:
        for run_id in repository.list_pending_run_ids():
            asyncio.create_task(job_runner.process_pending_jobs(run_id))
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_format)
    setup_observability(settings)
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id", "X-Trace-Id"],
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        session_cookie=settings.session_cookie_name,
        max_age=settings.session_max_age_seconds,
        same_site="lax",
        https_only=False,
    )
    repository = WorkflowRepository(settings.database_path, settings.demo_api_key, settings.demo_email, settings.demo_password)
    integration_manager = IntegrationManager(settings)
    job_runner = JobRunner(repository, integration_manager, settings.worker_poll_interval_ms)
    rate_limiter = SlidingWindowRateLimiter(settings.rate_limit_per_minute)
    app.state.repository = repository
    app.state.job_runner = job_runner
    app.state.settings = settings
    app.state.rate_limiter = rate_limiter
    app.state.tracer = get_tracer()

    if not repository.has_runs():
        account = repository.get_default_account()
        for item in seed_requests():
            run = WorkflowEngine.run(DataNormalizer.from_request(item))
            run.account_id = account.id
            repository.save_run(run)

    static_dir = Path(__file__).resolve().parent.parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.middleware("http")
    async def observability_and_throttling(request: Request, call_next):
        if request.url.path.startswith("/static"):
            return await call_next(request)

        trace_context = new_trace_context()
        request.state.request_id = trace_context.request_id
        request.state.trace_id = trace_context.trace_id

        identity = request.headers.get("X-RelayOps-Api-Key") or (request.client.host if request.client else "anonymous")
        started = time.perf_counter()
        if request.url.path.startswith("/api") and request.url.path != "/metrics":
            if not rate_limiter.allow(identity):
                observe_request(request.method, request.url.path, 429, time.perf_counter() - started)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Slow down and retry in a minute."},
                    headers={"X-Request-Id": trace_context.request_id, "X-Trace-Id": trace_context.trace_id},
                )

        tracer = app.state.tracer
        try:
            with tracer.start_as_current_span(f"{request.method} {request.url.path}") as span:
                span.set_attribute("http.method", request.method)
                span.set_attribute("http.route", request.url.path)
                span.set_attribute("relayops.request_id", trace_context.request_id)
                response = await call_next(request)
                span.set_attribute("http.status_code", response.status_code)
        except Exception as exc:  # pragma: no cover - defensive path
            capture_exception(exc)
            observe_request(request.method, request.url.path, 500, time.perf_counter() - started)
            raise

        duration = time.perf_counter() - started
        observe_request(request.method, request.url.path, response.status_code, duration)
        response.headers["X-Request-Id"] = trace_context.request_id
        response.headers["X-Trace-Id"] = trace_context.trace_id
        return response

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        capture_exception(exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "RelayOps hit an unexpected error.", "request_id": getattr(request.state, "request_id", None)},
        )

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.get("/settings")
    async def settings_page() -> FileResponse:
        return FileResponse(static_dir / "settings.html")

    @app.get("/metrics")
    async def metrics() -> Response:
        return metrics_response()

    @app.post("/api/auth/login", response_model=AuthResponse)
    async def login(payload: LoginRequest, request: Request) -> AuthResponse:
        account = repository.get_account_by_email(payload.email)
        if not account or not verify_password(payload.password, account.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        session = repository.create_session(account.id, session_expiry(settings))
        request.session["relayops_session_id"] = session.id
        return AuthResponse(account=account, auth_mode="session", message="Workspace session created.")

    @app.post("/api/auth/register", response_model=AuthResponse)
    async def register(payload: RegisterRequest, request: Request) -> AuthResponse:
        if repository.get_account_by_email(payload.email):
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        account = repository.create_account(payload.name, payload.email, f"relayops-{uuid4().hex[:16]}", password=payload.password)
        session = repository.create_session(account.id, session_expiry(settings))
        request.session["relayops_session_id"] = session.id
        return AuthResponse(account=account, auth_mode="session", message="Workspace created and signed in.")

    @app.post("/api/auth/logout")
    async def logout(request: Request):
        session_id = request.session.get("relayops_session_id")
        if session_id:
            repository.delete_session(session_id)
        request.session.clear()
        return {"message": "Signed out."}

    @app.get("/api/overview", response_model=OverviewResponse)
    async def overview(current_account=Depends(get_current_account)) -> OverviewResponse:
        runs = repository.list_runs(current_account.id)
        health = repository.health(current_account.id)
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
                "Workspace sessions, rate limiting, and observability telemetry",
            ],
            recent_runs=runs[:4],
        )

    @app.get("/api/runs")
    async def list_runs(current_account=Depends(get_current_account)):
        return repository.list_runs(current_account.id)

    @app.get("/api/health", response_model=HealthResponse)
    async def health(current_account=Depends(get_current_account)) -> HealthResponse:
        return repository.health(current_account.id)

    @app.get("/api/integrations", response_model=IntegrationStatusResponse)
    async def integrations(current_account=Depends(get_current_account)) -> IntegrationStatusResponse:
        return integration_manager.status()

    @app.get("/api/integrations/runtime", response_model=RuntimeSettingsResponse)
    async def integrations_runtime(current_account=Depends(get_current_account)) -> RuntimeSettingsResponse:
        return integration_manager.runtime_settings()

    @app.post("/api/integrations/check", response_model=IntegrationCheckResponse)
    async def integrations_check(current_account=Depends(get_current_account)) -> IntegrationCheckResponse:
        return await integration_manager.check_integrations()

    @app.get("/api/account", response_model=AccountResponse)
    async def account(request: Request, current_account=Depends(get_current_account)) -> AccountResponse:
        return AccountResponse(account=current_account, auth_mode=getattr(request.state, "auth_mode", "demo"))

    @app.get("/api/jobs")
    async def jobs(current_account=Depends(get_current_account)):
        return repository.list_jobs(account_id=current_account.id)

    @app.post("/api/webhooks/intake")
    async def intake_webhook(intake: IntakePayload, background_tasks: BackgroundTasks, current_account=Depends(get_current_account)):
        record = DataNormalizer.normalize(intake)
        run = WorkflowEngine.run(record)
        run.account_id = current_account.id
        run.status = "queued"
        repository.save_run(run)
        for provider in ("openai", "hubspot", "slack"):
            repository.enqueue_job(run.id, provider)
        if settings.run_jobs_in_web:
            background_tasks.add_task(job_runner.process_pending_jobs, run.id)
        return run

    @app.post("/api/workflows/execute")
    async def execute_workflow(request_payload: WorkflowRequest, background_tasks: BackgroundTasks, current_account=Depends(get_current_account)):
        record = DataNormalizer.from_request(request_payload)
        run = WorkflowEngine.run(record)
        run.account_id = current_account.id
        run.status = "queued"
        repository.save_run(run)
        for provider in ("openai", "hubspot", "slack"):
            repository.enqueue_job(run.id, provider)
        if settings.run_jobs_in_web:
            background_tasks.add_task(job_runner.process_pending_jobs, run.id)
        return run

    return app


app = create_app()
