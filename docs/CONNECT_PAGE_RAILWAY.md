# /connect page and Playwright on Railway

## Why you were getting 404

The **Connect** page and backend **POST /connect-skool** were added in code but **never committed or pushed**. Railway was still building from an older commit that had no `/connect` route, so the app showed "Oops! Page not found" (the React `NotFound` component).

**Fix applied:** All connect-related changes were committed and pushed to `dev` (commit `db35b1f`):

- **Frontend:** `ConnectPage.tsx`, `/connect` route in `App.tsx`, `api.connectSkool` and 70s timeout in `api.ts`
- **Backend:** `POST /connect-skool`, `ConnectSkoolModel`, profile `source`/`connected_at` columns and model fields, `ensure_tables()` migration for new columns

After Railway **redeploys** both **engageflow front** and **engageflow back** from `dev`, you should get:

- **https://engageflow-front-dev.up.railway.app/connect** → Connect Skool page (email/password form)
- Submitting the form → `POST` to backend `VITE_BACKEND_URL/connect-skool` → create profile (`source='micro'`, `status='paused'`) → Playwright login → cookies stored; or 400 with error message

## Playwright and browser on the backend

The **backend** already has Playwright and Chromium in the image:

- **backend/Dockerfile** includes:  
  `RUN python -m playwright install --with-deps chromium`

So the engageflow back service on Railway runs with Chromium installed. `check_login` (used by `/connect-skool`) uses headless Chromium via the engine’s Skool session flow.

**If** you see failures only on Railway (e.g. timeouts, "Browser not found", or crashes):

- Railway’s environment can be more constrained (memory, `/dev/shm`). The Dockerfile uses the standard Playwright install; if needed, you can add env for larger shared memory or use a Playwright Docker base image later.
- Ensure the **backend** service has enough memory (e.g. 1GB+); Chromium can be heavy.

No code changes were required for Playwright; the existing Dockerfile is correct for the connect flow.

## Quick check after deploy

1. Open **https://engageflow-front-dev.up.railway.app/connect** → you should see the Connect Skool form, not 404.
2. Submit email + password → request goes to backend; if login succeeds you get "Connected"; if not, you get the backend error message (no more 404 for the page itself).
