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

## Optional live integrations

RelayOps supports optional live integrations through environment variables. Copy `.env.example` values into your local environment before starting the app.

- `OPENAI_API_KEY`: enables OpenAI-generated operational summaries
- `OPENAI_MODEL`: optional OpenAI model override
- `SLACK_WEBHOOK_URL`: enables Slack incoming webhook notifications
- `HUBSPOT_PRIVATE_APP_TOKEN`: enables HubSpot CRM contact sync
- `HUBSPOT_BASE_URL`: optional HubSpot API base URL override

If these variables are not set, the app keeps deterministic local behavior and marks integrations as disabled in the UI.

Use `/settings` to run connector checks and detect obvious misconfiguration such as invalid HubSpot auth or malformed Slack webhook URLs.

## Validate locally

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall app
```

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
