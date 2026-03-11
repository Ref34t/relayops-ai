# RelayOps AI

RelayOps AI is a SaaS-style portfolio project tailored to the 9H AI & Integration Specialist role. It demonstrates how messy operational data can be ingested from client systems, normalized, routed through workflow logic, and turned into decision-ready operational briefs.

## Product summary

RelayOps acts as an AI workflow and integration layer for operations teams working across fragmented tools such as CRMs, forms, finance systems, and internal collaboration platforms.

The MVP models a realistic business flow:

- inbound webhook or intake payload arrives from a client system
- inconsistent fields are normalized into a clean internal schema
- workflow logic scores urgency and generates next actions
- the system produces an AI-style operational brief for stakeholders
- the frontend presents recent runs and a live workflow demo
- workflow history is persisted in SQLite with audit and sync metadata

## Why this project fits 9H

- AI workflows: generates concise operational briefs from normalized client data
- Integrations mindset: models webhook intake, CRM sync, async task execution, and downstream notifications
- Backend focus: FastAPI service with typed models, orchestration logic, and structured logging
- Delivery thinking: polished UI that explains the architecture and shows the workflow in action

## Architecture

- `app/main.py`: FastAPI app, API routes, and static file serving
- `app/models.py`: typed request and response contracts
- `app/services.py`: normalization logic, workflow engine, audit events, and sync simulation
- `app/repository.py`: SQLite-backed workflow persistence and health reporting
- `app/config.py`: runtime settings for app configuration
- `static/index.html`: SaaS-style product page and live demo shell
- `static/styles.css`: visual system and responsive layout
- `static/app.js`: frontend data loading and workflow submission
- `tests/test_app.py`: executable validation of key app behavior

## Demo flow

1. A messy lead or ops payload is received through a webhook endpoint.
2. The backend normalizes inconsistent field names and missing values.
3. The workflow engine scores urgency, determines actions, and composes an AI-ready brief.
4. A client dashboard visualizes recent workflow runs and operational recommendations.

## Stack

- Python 3.11+
- FastAPI
- Uvicorn
- SQLite
- Vanilla HTML/CSS/JS frontend served by the backend

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8012
```

Then open `http://127.0.0.1:8012`.

## Optional live integrations

RelayOps supports optional live integrations through environment variables. Copy `.env.example` values into your local environment before starting the app.

- `OPENAI_API_KEY`: enables OpenAI-generated operational summaries
- `OPENAI_MODEL`: optional OpenAI model override
- `SLACK_WEBHOOK_URL`: enables Slack incoming webhook notifications
- `HUBSPOT_PRIVATE_APP_TOKEN`: enables HubSpot CRM contact sync
- `HUBSPOT_BASE_URL`: optional HubSpot API base URL override

If these variables are not set, the app keeps deterministic local behavior and marks integrations as disabled in the UI.

## Validate locally

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall app
```

## Key endpoints

- `GET /api/overview`
- `GET /api/health`
- `POST /api/webhooks/intake`
- `POST /api/workflows/execute`
- `GET /api/runs`

## Product layers now included

- Intake layer: webhook-style ingestion for raw business payloads
- Normalization layer: alias mapping and messy-data cleanup
- Workflow layer: scoring, action generation, and AI-style brief creation
- Persistence layer: SQLite-backed workflow history
- Ops layer: health reporting, audit events, and sync result tracking
- Presentation layer: SaaS-style product interface with live workflow execution

## Suggested portfolio framing

When presenting this project, position it as:

> An AI-powered workflow and integration layer that unifies fragmented business inputs, cleans operational data, and produces action-ready briefs across client systems.
