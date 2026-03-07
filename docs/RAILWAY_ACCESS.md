# Railway Access — Cursor Autonomy

**Project:** efficient-ambition | **Service (backend):** engageflow | **Project ID:** `f2cddd1a-3d44-47f6-bd18-5ce566b88da4`

## Full access for Cursor (configured)

Cursor **can** access Railway in two ways:

1. **Railway CLI** — After one-time `railway login` and `railway link`, Cursor can run `railway status`, `railway logs`, `railway redeploy`, etc. Credentials are in `~/.railway/config.json`.
2. **Railway GraphQL API** — The same account token (from config or `RAILWAY_API_TOKEN` in env) can be used for `https://backboard.railway.com/graphql/v2` to rename services, set root directory, redeploy, etc. **No dashboard clicks required.** Token in config is under **`.user.token`** (not at root). See JOINER_SOURCE_FIX_PROOF.md and `scripts/railway-joiner-source-update.json`.

GitHub Secrets (RAILWAY_TOKEN, RAILWAY_API_TOKEN, RAILWAY_PROJECT_ID) are used by CI/workflows when present; local Cursor uses `railway login` token or `RAILWAY_API_TOKEN` for API calls.

## One-time local login (if not already done)

Run once in your terminal (from repo root):

```bash
railway login
railway link --project f2cddd1a-3d44-47f6-bd18-5ce566b88da4 --service engageflow --environment DEV
```

After that, Cursor can run:

- `railway status`
- `railway logs --service engageflow` (streams; pipe to `head -N` to limit)
- `./scripts/railway-info.sh`
- GraphQL API calls (rename services, serviceInstanceUpdate, serviceInstanceRedeploy) using token from `~/.railway/config.json` or `RAILWAY_API_TOKEN`.

## GitHub Actions (when workflow exists)

If a workflow uses Railway, it typically uses:

| Secret | Purpose |
|--------|---------|
| RAILWAY_API_TOKEN | `railway link` (account token). Create at: https://railway.app/account/tokens |
| RAILWAY_TOKEN | `railway variable set` for DEV |
| RAILWAY_TOKEN_PROD | `railway variable set` for production |
| RAILWAY_PROJECT_ID | `f2cddd1a-3d44-47f6-bd18-5ce566b88da4` |

Add `RAILWAY_API_TOKEN` to GitHub Secrets. Without it, the "Link project" step fails.
