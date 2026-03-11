# RelayOps

RelayOps is an AI-powered workflow and integration layer for operations teams working across fragmented business systems. It accepts messy inbound records, normalizes them into a consistent internal schema, orchestrates decision logic, and produces action-ready operational briefs with audit and sync visibility.

## Product summary

RelayOps acts as an AI workflow and integration layer for operations teams working across fragmented tools such as CRMs, forms, finance systems, and internal collaboration platforms.

The MVP models a realistic business flow:

- inbound webhook or intake payload arrives from a client system
- inconsistent fields are normalized into a clean internal schema
- workflow logic scores urgency and generates next actions
- the system produces an AI-style operational brief for stakeholders
- the frontend presents recent runs and a live workflow demo
- workflow history is persisted in SQLite with audit and sync metadata

## Features

- Webhook-style intake for fragmented business payloads
- Normalization layer for inconsistent fields and incomplete data
- Workflow scoring and action generation
- Persistent run history backed by SQLite
- Database migration bootstrap for schema creation
- Demo account and API-key based auth model
- Persisted background job queue for external integrations
- Health reporting, audit trail, and sync visibility
- Optional live integrations for OpenAI, Slack, and HubSpot
- Dedicated settings page for connector diagnostics and setup guidance
- SaaS-style frontend for live demo and operational review

## Architecture

- `app/main.py`: FastAPI app, API routes, and static file serving
- `app/models.py`: typed request and response contracts
- `app/services.py`: normalization logic, workflow engine, audit events, and sync simulation
- `app/repository.py`: SQLite-backed workflow persistence and health reporting
- `app/migrations.py`: migration bootstrap and schema registration
- `app/auth.py`: demo account and API-key resolution
- `app/jobs.py`: persisted background job processing for integrations
- `app/worker.py`: standalone worker process for queued integration jobs
- `app/config.py`: runtime settings for app configuration
- `static/index.html`: SaaS-style product page and live demo shell
- `static/styles.css`: visual system and responsive layout
- `static/app.js`: frontend data loading and workflow submission
- `tests/test_app.py`: executable validation of key app behavior

## Demo flow

1. A webhook or intake payload arrives from a client system.
2. The backend normalizes inconsistent field names and missing values.
3. The workflow engine scores urgency, determines actions, and composes an operational brief.
4. Integration work is queued as persisted background jobs instead of running inline in the request.
5. Optional integrations enrich the run with live summaries and downstream sync attempts.
6. The dashboard visualizes recent runs, audit events, health, and sync outcomes.

## Stack

- Python 3.11+
- FastAPI
- Uvicorn
- SQLite
- Vanilla HTML/CSS/JS frontend served by the backend

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

Demo account:

- default workspace: `RelayOps Demo Workspace`
- default API key: `relayops-demo-key`

You can send the API key through the `X-RelayOps-Api-Key` header, although the local UI falls back to the demo workspace automatically.

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
- `RELAYOPS_LOG_FORMAT`: `text` or `json`

## Optional live integrations

RelayOps supports optional live integrations through environment variables. Copy `.env.example` values into your local environment before starting the app.

- `OPENAI_API_KEY`: enables OpenAI-generated operational summaries
- `OPENAI_MODEL`: optional OpenAI model override
- `SLACK_WEBHOOK_URL`: enables Slack incoming webhook notifications
- `HUBSPOT_PRIVATE_APP_TOKEN`: enables HubSpot CRM contact sync
- `HUBSPOT_BASE_URL`: optional HubSpot API base URL override

If these variables are not set, the app keeps deterministic local behavior and marks integrations as disabled in the UI.

Use `/settings` to run connector checks and detect obvious misconfiguration such as invalid HubSpot auth or malformed Slack webhook URLs.

## Workflow and job statuses

Workflow run statuses:

- `queued`: the request was accepted and integration work was added to the persisted job queue
- `completed`: all queued integration jobs finished successfully
- `degraded`: the workflow finished, but one or more integration jobs failed

Job statuses:

- `pending`: waiting to be processed
- `processing`: claimed by the in-process worker
- `completed`: processed successfully
- `failed`: processing failed and the workflow was marked degraded

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
python3 -m compileall app
```

## Quality gates

- backend tests via `unittest`
- bytecode/import validation via `compileall`
- GitHub Actions workflow for tests and compile checks

## Troubleshooting

- `401 Unauthorized` from `/api/account` or workflow endpoints:
  clear the stored browser workspace key or send a valid `X-RelayOps-Api-Key` header
- HubSpot shows `misconfigured` in `/settings`:
  confirm the private app token is valid and includes CRM contact scopes
- Slack shows `misconfigured`:
  verify `SLACK_WEBHOOK_URL` starts with `https://hooks.slack.com/services/`
- OpenAI checks fail:
  confirm `OPENAI_API_KEY` is valid and the configured `OPENAI_MODEL` is reachable
- Old local database causes schema errors:
  restart the app after pulling the latest code so migrations apply to the existing SQLite file

## Key endpoints

- `GET /api/overview`
- `GET /api/health`
- `GET /api/account`
- `GET /api/integrations`
- `GET /api/jobs`
- `POST /api/integrations/check`
- `POST /api/webhooks/intake`
- `POST /api/workflows/execute`
- `GET /api/runs`

## Product layers now included

- Intake layer: webhook-style ingestion for raw business payloads
- Normalization layer: alias mapping and messy-data cleanup
- Workflow layer: scoring, action generation, and brief creation
- Persistence layer: SQLite-backed workflow history
- Migration layer: schema bootstrap through migration registration
- Account layer: demo workspace plus API-key based account resolution
- Queue layer: background job records for external integrations
- Ops layer: health reporting, audit events, and sync result tracking
- Presentation layer: SaaS-style product interface with live workflow execution

## Use cases

- Lead and operations intake across multiple tools
- Internal service delivery orchestration
- AI-assisted summaries for operations teams
- Downstream notifications and CRM sync visibility
