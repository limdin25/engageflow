# Railway Access — Cursor Autonomy

**Project:** efficient-ambition | **Service (backend):** engageflow | **Project ID:** `f2cddd1a-3d44-47f6-bd18-5ce566b88da4`

## Why Cursor Can't Access Railway Directly

1. **RAILWAY_TOKEN (project token)** — Works in GitHub Actions for `railway variable set` / `railway up`. Does **not** work for `railway link` locally; that needs account-level auth.
2. **No Railway UI** — Cursor cannot open the Railway dashboard.
3. **Token in .railway-secrets** — Returns "Unauthorized" for `railway link` / `railway status`; project tokens are for deploy/CI, not interactive CLI.

## Fix: One-Time Local Login

Run once in your terminal (from repo root):

```bash
railway login
railway link --project f2cddd1a-3d44-47f6-bd18-5ce566b88da4 --service engageflow --environment DEV
```

After that, Cursor can run:

- `railway status`
- `railway logs --service engageflow` (streams; pipe to `head -N` to limit)
- `./scripts/railway-info.sh`

Credentials are cached. Cursor's terminal uses your shell, so it inherits access.

## GitHub Actions

The workflow (`.github/workflows/railway.yml`) uses:

| Secret | Purpose |
|--------|---------|
| RAILWAY_API_TOKEN | `railway link` (account token). Create at: https://railway.app/account/tokens |
| RAILWAY_TOKEN | `railway variable set` for DEV |
| RAILWAY_TOKEN_PROD | `railway variable set` for production |
| RAILWAY_PROJECT_ID | `f2cddd1a-3d44-47f6-bd18-5ce566b88da4` |

Add `RAILWAY_API_TOKEN` to GitHub Secrets. Without it, the "Link project" step fails.
