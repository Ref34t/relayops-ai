# RelayOps

RelayOps is an AI-powered workflow and integration layer for operations teams working across fragmented business systems. It accepts messy inbound records, normalizes them into a consistent internal schema, orchestrates decision logic, and produces action-ready operational briefs with audit, sync, and observability visibility.

## Product summary

RelayOps models a realistic operations workflow:

- inbound webhook or intake payload arrives from a client system
- inconsistent fields are normalized into a clean internal schema
- workflow logic scores urgency and generates next actions
- the system produces an operational brief plus structured AI analysis
- background jobs handle AI enrichment and downstream sync work
- workflow history, sessions, jobs, and diagnostics are persisted in SQLite

## Features

- Webhook-style intake for fragmented business payloads
- Normalization layer for inconsistent fields and incomplete data
- Workflow scoring, action generation, and AI analysis
- Persistent run history backed by SQLite
- Formal Alembic migrations for schema creation and upgrades
- Session-based auth with cookie login plus API-key overrides
- Persisted background job queue with retries, leases, and worker mode
- Health reporting, audit trail, and sync visibility
- Prometheus metrics, tracing hooks, and optional Sentry error reporting
- Request throttling for API abuse protection
- Optional live integrations for OpenAI, Slack, and HubSpot
- Dedicated settings page for connector diagnostics and setup guidance
- Playwright browser tests for live UI flows

## Architecture

- `app/main.py`: FastAPI app, middleware, auth routes, API routes, and static file serving
- `app/models.py`: typed request and response contracts
- `app/services.py`: normalization logic, workflow engine, audit events, and sync simulation
- `app/repository.py`: SQLite-backed workflow, account, session, and job persistence
- `app/migrations.py`: Alembic runner used during startup
- `alembic/`: migration environment and revision history
- `app/auth.py`: password hashing, session expiry, and account resolution
- `app/jobs.py`: persisted background job processing with retries and worker leases
- `app/worker.py`: standalone worker process for queued integration jobs
- `app/observability.py`: metrics, tracing, error reporting, and rate limiting primitives
- `app/config.py`: runtime settings for app configuration
- `static/index.html`: product dashboard and live workflow shell
- `static/settings.html`: connector diagnostics view
- `static/app.js`: session UX, workflow execution, and dashboard rendering
- `frontend-tests/`: Playwright end-to-end browser suite
- `tests/test_app.py`: backend validation suite

## Demo flow

1. A webhook or intake payload arrives from a client system.
2. The backend normalizes inconsistent field names and missing values.
3. The workflow engine scores urgency, determines actions, and composes an operational brief.
4. Integration work is queued as persisted background jobs instead of running inline in the request.
5. Optional integrations enrich the run with live summaries and downstream sync attempts.
6. The dashboard visualizes recent runs, audit events, health, sync outcomes, and workspace context.

## Stack

- Python 3.11+
- FastAPI
- SQLite
- Alembic
- OpenTelemetry
- Prometheus client
- Sentry SDK
- Vanilla HTML/CSS/JS
- Playwright

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8012
```

Then open `http://127.0.0.1:8012`.

Available pages:

- `/` product dashboard
- `/settings` integration settings and connector diagnostics
- `/metrics` Prometheus metrics endpoint

Demo account:

- default workspace: `RelayOps Demo Workspace`
- default email: `demo@relayops.app`
- default password: `relayops-demo-pass`
- default API key: `relayops-demo-key`

## Authentication model

- browser users sign in through `POST /api/auth/login`, which creates an HttpOnly session cookie
- new local workspaces can be created with `POST /api/auth/register`
- `POST /api/auth/logout` clears the current session
- machine-to-machine clients can use `X-RelayOps-Api-Key`
- if neither session nor API key is present, the local UI falls back to the seeded demo workspace

To run migrations manually:

```bash
alembic upgrade head
```

## Worker mode

RelayOps supports two queue-processing modes:

- default dev mode: the web process also processes jobs
- worker mode: disable job execution in web and run a separate worker process

Run with a separate worker:

```bash
export RELAYOPS_RUN_JOBS_IN_WEB=0
uvicorn app.main:app --reload --port 8012
python -m app.worker
```

Operational settings:

- `RELAYOPS_RUN_JOBS_IN_WEB`: `1` or `0`
- `RELAYOPS_WORKER_POLL_INTERVAL_MS`: worker polling interval in milliseconds
- `RELAYOPS_RATE_LIMIT_PER_MINUTE`: API requests allowed per identity per minute
- `RELAYOPS_SESSION_SECRET`: cookie-signing secret
- `RELAYOPS_SESSION_MAX_AGE_SECONDS`: browser session lifetime
- `RELAYOPS_LOG_FORMAT`: `text` or `json`
- `RELAYOPS_TRACE_EXPORTER`: `disabled`, `console`, or `otlp`
- `RELAYOPS_OTLP_ENDPOINT`: OTLP HTTP exporter endpoint when tracing is set to `otlp`
- `SENTRY_DSN`: enables Sentry error reporting

## Optional live integrations

RelayOps supports optional live integrations through environment variables. Copy `.env.example` values into your local environment before starting the app.

- `OPENAI_API_KEY`: enables OpenAI-generated operational summaries
- `OPENAI_MODEL`: optional OpenAI model override
- `SLACK_WEBHOOK_URL`: enables Slack incoming webhook notifications
- `HUBSPOT_PRIVATE_APP_TOKEN`: enables HubSpot CRM contact sync
- `HUBSPOT_BASE_URL`: optional HubSpot API base URL override

If these variables are not set, the app keeps deterministic local behavior and marks integrations as disabled in the UI.

## Observability

- `GET /metrics`: Prometheus-compatible request and job metrics
- request tracing: enabled through OpenTelemetry when `RELAYOPS_TRACE_EXPORTER` is configured
- error reporting: optional Sentry integration through `SENTRY_DSN`
- response headers: every request includes `X-Request-Id` and `X-Trace-Id`

## Workflow and job statuses

Workflow run statuses:

- `queued`: the request was accepted and integration work was added to the persisted job queue
- `completed`: all queued integration jobs finished successfully
- `degraded`: the workflow finished, but one or more integration jobs failed

Job statuses:

- `pending`: waiting to be processed
- `processing`: claimed by a worker lease
- `completed`: processed successfully
- `failed`: processing exhausted retries and the workflow was marked degraded

## Example payloads

Direct workflow execution:

```json
{
  "source": "hubspot",
  "company": "Atlas Retail Ops",
  "contact_name": "Laila Fathy",
  "email": "laila@atlasretail.ai",
  "pain_points": ["Manual reporting", "Slow approvals"],
  "requested_systems": ["HubSpot", "NetSuite", "Slack"],
  "monthly_revenue": "EUR 90k-140k",
  "urgency": "high",
  "notes": "Leadership needs a weekly summary."
}
```

Webhook intake with inconsistent field names:

```json
{
  "source": "typeform",
  "payload": {
    "company_name": "Cairo Service Desk",
    "full_name": "Nour Tarek",
    "work_email": "nour@example.com",
    "issues": "Manual reporting, missing visibility",
    "requestedTools": ["HubSpot", "Slack"],
    "priority": "urgent",
    "brief": "Needs better routing."
  }
}
```

Example local request with API key:

```bash
curl -X POST http://127.0.0.1:8012/api/workflows/execute \
  -H "Content-Type: application/json" \
  -H "X-RelayOps-Api-Key: relayops-demo-key" \
  -d @payload.json
```

## Validate locally

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall app tests
npm install
npm run test:e2e
```

The browser suite validates:

- session login and workspace-aware dashboard rendering
- workflow submission from the UI
- connector diagnostics from `/settings`

## Quality gates

- backend tests via `unittest`
- frontend browser tests via Playwright
- bytecode/import validation via `compileall`
- GitHub Actions workflow for backend and frontend validation

## Troubleshooting

- `401 Unauthorized` from `/api/account` or workflow endpoints:
  sign in again, clear the stored browser workspace key, or send a valid `X-RelayOps-Api-Key` header
- `429 Too Many Requests` from API routes:
  lower the request frequency or increase `RELAYOPS_RATE_LIMIT_PER_MINUTE` for local testing
- HubSpot shows `misconfigured` in `/settings`:
  confirm the private app token is valid and includes CRM contact scopes
- Slack shows `misconfigured`:
  verify `SLACK_WEBHOOK_URL` starts with `https://hooks.slack.com/services/`
- OpenAI checks fail:
  confirm `OPENAI_API_KEY` is valid and the configured `OPENAI_MODEL` is reachable
- Old local database causes schema errors:
  run `alembic upgrade head` or restart the app so Alembic applies the latest revisions

## Key endpoints

- `GET /api/overview`
- `GET /api/health`
- `GET /api/account`
- `POST /api/auth/login`
- `POST /api/auth/register`
- `POST /api/auth/logout`
- `GET /api/integrations`
- `GET /api/jobs`
- `POST /api/integrations/check`
- `POST /api/webhooks/intake`
- `POST /api/workflows/execute`
- `GET /api/runs`
- `GET /metrics`

## Product layers now included

- Intake layer: webhook-style ingestion for raw business payloads
- Normalization layer: alias mapping and messy-data cleanup
- Workflow layer: scoring, action generation, and brief creation
- Persistence layer: SQLite-backed workflow, session, and job history
- Migration layer: Alembic-managed schema revisions
- Account layer: session login, workspace creation, and API-key resolution
- Queue layer: durable job records with retries and worker leases
- Ops layer: health reporting, audit events, and sync result tracking
- Observability layer: Prometheus metrics, tracing hooks, and Sentry integration
- Protection layer: rate limiting for API abuse control
- Presentation layer: SaaS-style product interface with live workflow execution

## Use cases

- Lead and operations intake across multiple tools
- Internal service delivery orchestration
- AI-assisted summaries for operations teams
- Downstream notifications and CRM sync visibility
