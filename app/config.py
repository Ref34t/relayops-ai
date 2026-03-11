from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Settings:
    app_name: str = "RelayOps AI"
    database_path: Path = Path("data/relayops.db")
    demo_api_key: str = "relayops-demo-key"
    demo_email: str = "demo@relayops.app"
    demo_password: str = "relayops-demo-pass"
    run_jobs_in_web: bool = True
    worker_poll_interval_ms: int = 1000
    log_format: str = "text"
    session_cookie_name: str = "relayops_session"
    session_secret: str = "relayops-session-secret"
    session_max_age_seconds: int = 60 * 60 * 8
    rate_limit_per_minute: int = 60
    trace_exporter: str = "disabled"
    otlp_endpoint: Optional[str] = None
    sentry_dsn: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    slack_webhook_url: Optional[str] = None
    hubspot_private_app_token: Optional[str] = None
    hubspot_base_url: str = "https://api.hubapi.com"


def get_settings() -> Settings:
    return Settings(
        database_path=Path(os.getenv("RELAYOPS_DB_PATH", "data/relayops.db")),
        demo_api_key=os.getenv("RELAYOPS_DEMO_API_KEY", "relayops-demo-key"),
        demo_email=os.getenv("RELAYOPS_DEMO_EMAIL", "demo@relayops.app"),
        demo_password=os.getenv("RELAYOPS_DEMO_PASSWORD", "relayops-demo-pass"),
        run_jobs_in_web=os.getenv("RELAYOPS_RUN_JOBS_IN_WEB", "1") not in {"0", "false", "False"},
        worker_poll_interval_ms=int(os.getenv("RELAYOPS_WORKER_POLL_INTERVAL_MS", "1000")),
        log_format=os.getenv("RELAYOPS_LOG_FORMAT", "text"),
        session_cookie_name=os.getenv("RELAYOPS_SESSION_COOKIE", "relayops_session"),
        session_secret=os.getenv("RELAYOPS_SESSION_SECRET", "relayops-session-secret"),
        session_max_age_seconds=int(os.getenv("RELAYOPS_SESSION_MAX_AGE_SECONDS", str(60 * 60 * 8))),
        rate_limit_per_minute=int(os.getenv("RELAYOPS_RATE_LIMIT_PER_MINUTE", "60")),
        trace_exporter=os.getenv("RELAYOPS_TRACE_EXPORTER", "disabled"),
        otlp_endpoint=os.getenv("RELAYOPS_OTLP_ENDPOINT"),
        sentry_dsn=os.getenv("SENTRY_DSN"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
        hubspot_private_app_token=os.getenv("HUBSPOT_PRIVATE_APP_TOKEN"),
        hubspot_base_url=os.getenv("HUBSPOT_BASE_URL", "https://api.hubapi.com"),
    )
