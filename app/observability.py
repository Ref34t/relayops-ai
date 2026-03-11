from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
from uuid import uuid4

import sentry_sdk
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sentry_sdk.integrations.logging import LoggingIntegration
from starlette.responses import Response

from app.config import Settings

REQUEST_COUNT = Counter("relayops_http_requests_total", "HTTP requests served", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("relayops_http_request_duration_seconds", "HTTP request latency", ["method", "path"])
JOB_COUNT = Counter("relayops_jobs_total", "Jobs processed", ["provider", "status"])


@dataclass
class TraceContext:
    request_id: str
    trace_id: str


class SlidingWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.buckets: dict[str, deque[float]] = defaultdict(deque)
        self.lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self.lock:
            bucket = self.buckets[key]
            while bucket and now - bucket[0] > self.window_seconds:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return False
            bucket.append(now)
            return True


def setup_observability(settings: Settings) -> None:
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            traces_sample_rate=1.0 if settings.trace_exporter != "disabled" else 0.0,
            integrations=[LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)],
        )

    if settings.trace_exporter == "disabled":
        return

    provider = TracerProvider(resource=Resource.create({"service.name": "relayops-ai"}))
    if settings.trace_exporter == "otlp" and settings.otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint)
    else:
        exporter = ConsoleSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def get_tracer():
    return trace.get_tracer("relayops")


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def capture_exception(exc: Exception) -> None:
    if sentry_sdk.get_client().is_active():
        sentry_sdk.capture_exception(exc)


def observe_request(method: str, path: str, status_code: int, duration_seconds: float) -> None:
    REQUEST_COUNT.labels(method=method, path=path, status=str(status_code)).inc()
    REQUEST_LATENCY.labels(method=method, path=path).observe(duration_seconds)


def observe_job(provider: str, status: str) -> None:
    JOB_COUNT.labels(provider=provider, status=status).inc()


def new_trace_context() -> TraceContext:
    request_id = str(uuid4())
    return TraceContext(request_id=request_id, trace_id=request_id.replace("-", ""))
