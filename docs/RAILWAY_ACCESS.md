# Railway Access — Cursor Autonomy

## Why Cursor Can't Access Railway Directly

1. **RAILWAY_TOKEN (project token)** — Works in GitHub Actions for `railway variable set` / `railway up`. Does **not** work for `railway link` locally; that needs account-level auth.
2. **No Railway UI** — Cursor cannot open the Railway dashboard.
3. **Token in .railway-secrets** — Returns "Unauthorized" for `railway link` / `railway status`; project tokens are for deploy/CI, not interactive CLI.

## Fix: One-Time Local Login

Run once in your terminal:

```bash
cd /path/to/engageflow-repo
railway login
railway link --project f2cddd1a-3d44-47f6-bd18-5ce566b88da4 --service engageflow --environment DEV
```

After that, Cursor can run:

- `railway logs --service engageflow -n 50`
- `railway status`
- `./scripts/railway-info.sh`

Credentials are cached in `~/.railway/` (or similar). Cursor's terminal uses your shell, so it inherits access.

## GitHub Actions

The workflow now uses:
- **RAILWAY_API_TOKEN** — For `railway link` (account token). Create at: https://railway.app/account/tokens
- **RAILWAY_TOKEN** / **RAILWAY_TOKEN_PROD** — For `railway variable set` (project tokens)

Add `RAILWAY_API_TOKEN` to GitHub Secrets. Without it, the "Link project" step fails.
