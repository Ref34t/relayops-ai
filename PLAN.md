# RelayOps Execution Plan

## Objective

Build a presentable MVP of RelayOps by Thursday, March 12, 2026. The product should feel like a real SaaS platform and demonstrate both engineering depth and strong visual/product quality for the 9H AI & Integration Specialist role.

## Product Positioning

RelayOps is an AI workflow and integration layer for operations teams dealing with fragmented business systems. It ingests messy records from multiple tools, normalizes them, routes them through workflow logic, and produces decision-ready operational briefs.

## Proof Points For 9H

- Python backend engineering
- REST API and middleware design
- webhook-style intake flows
- data cleanup and normalization
- workflow orchestration logic
- AI-assisted outputs without overclaiming
- clear technical architecture communication

## MVP Scope

### Must include

- FastAPI backend
- typed request and response models
- webhook intake endpoint
- workflow execution endpoint
- normalization layer for messy payloads
- workflow scoring and action generation
- live frontend dashboard
- polished SaaS presentation
- realistic seeded runs
- README tailored to the 9H role

### Excluded from this version

- real model API integration
- auth and billing
- production database
- live third-party API credentials
- deployment automation

## Architecture

1. Frontend dashboard
   Presents the product narrative, architecture, business value, and recent workflow runs.

2. Inbound API layer
   Accepts webhook payloads and direct workflow requests.

3. Normalization layer
   Resolves inconsistent field names, missing values, and malformed list-like inputs.

4. Workflow engine
   Scores urgency, recommends actions, and constructs operational summaries.

5. Run history store
   Holds seeded and newly created runs for demo purposes.

## Phased Execution

### Phase 1: Planning and repo structure

- add this plan file
- keep repo structure minimal and presentation-ready

### Phase 2: Backend MVP

- implement FastAPI app
- add models for intake, normalized records, actions, and runs
- build normalization and workflow services
- expose overview, runs, webhook, and workflow execution endpoints
- verify locally with `uvicorn`

### Phase 3: Frontend MVP

- build a distinctive SaaS-style UI
- connect overview and run history to backend APIs
- add interactive workflow form
- verify locally in browser

### Phase 4: Packaging and polish

- tighten copy for the 9H role
- finish README
- run an end-to-end local check

## Validation Approach

After each major phase:

1. run the app locally
2. verify the relevant endpoints or UI behavior
3. ask for a quick browser test before moving on

## Deliverable Standard

A reviewer should understand within a minute that RelayOps is:

- a real SaaS-style concept
- built on a Python backend
- centered on integrations and workflow logic
- capable of handling messy operational data
- presented with product-quality polish
