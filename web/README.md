# RelayOps Frontend

This package contains the Next.js frontend for RelayOps.

## Purpose

The frontend provides:

- landing page
- workspace sign-in flow
- protected dashboard route
- protected settings route
- same-origin proxy to the FastAPI backend

## Routes

- `/` landing page
- `/signin` sign-in and workspace creation
- `/dashboard` protected operational workspace
- `/settings` protected integration settings
- `/api/[...path]` proxy to the backend API

## Development

Start the backend first:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8022
```

Then start the frontend:

```bash
npm install
RELAYOPS_BACKEND_URL=http://127.0.0.1:8022 npm run dev -- --port 3006
```

Open:

- [http://localhost:3006](http://localhost:3006)

## Production Build Check

```bash
npm run lint
npm run build
```

To run the production server locally after a build:

```bash
RELAYOPS_BACKEND_URL=http://127.0.0.1:8022 npm run start -- --port 3006
```

## Session Behavior

- the sign-in route creates a browser session through the backend
- `/dashboard` and `/settings` require a valid session
- unauthenticated access to protected routes redirects to `/signin`
- authenticated access to `/signin` redirects to `/dashboard`

## Proxy Behavior

The frontend does not call the Python backend directly from the browser.

Instead:

- browser requests go to Next.js
- Next.js proxies `/api/...` to `RELAYOPS_BACKEND_URL`
- cookies and headers are forwarded server-side
- responses are marked `no-store` to avoid stale auth state

## Important Files

- [page.tsx](/Volumes/PortableSSD/world/h6/web/src/app/page.tsx)
- [signin page](/Volumes/PortableSSD/world/h6/web/src/app/signin/page.tsx)
- [dashboard page](/Volumes/PortableSSD/world/h6/web/src/app/dashboard/page.tsx)
- [settings page](/Volumes/PortableSSD/world/h6/web/src/app/settings/page.tsx)
- [proxy route](/Volumes/PortableSSD/world/h6/web/src/app/api/[...path]/route.ts)
- [dashboard shell](/Volumes/PortableSSD/world/h6/web/src/components/dashboard-shell.tsx)
- [signin shell](/Volumes/PortableSSD/world/h6/web/src/components/signin-shell.tsx)
- [settings shell](/Volumes/PortableSSD/world/h6/web/src/components/settings-shell.tsx)
- [relayops client](/Volumes/PortableSSD/world/h6/web/src/lib/relayops.ts)
- [session helpers](/Volumes/PortableSSD/world/h6/web/src/lib/session.ts)
