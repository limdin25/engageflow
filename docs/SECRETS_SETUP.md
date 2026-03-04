# Railway Secrets — Add to GitHub

**One-time setup.** Add these to GitHub repo → Settings → Secrets and variables → Actions.

Values are in `.railway-secrets` (gitignored). Copy from there:

1. `RAILWAY_TOKEN` — dev (push to dev)
2. `RAILWAY_TOKEN_PROD` — production (push to main)
3. `RAILWAY_PROJECT_ID` — project ID

**Rotate tokens later** in Railway → Settings → Tokens, then update GitHub Secrets. Delete `.railway-secrets` after setup.
