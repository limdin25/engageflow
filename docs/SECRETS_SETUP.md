# Railway Secrets — Add to GitHub

**One-time setup.** Add these to GitHub repo → Settings → Secrets and variables → Actions.

Values are in `.railway-secrets` (gitignored). Copy from there:

1. `RAILWAY_TOKEN` — dev project token (push to dev)
2. `RAILWAY_TOKEN_PROD` — production project token (push to main)
3. `RAILWAY_PROJECT_ID` — project ID
4. `RAILWAY_API_TOKEN` — **account token** (for `railway link` in CI). From Railway → Account Settings → Tokens

**Rotate tokens later** in Railway → Settings → Tokens, then update GitHub Secrets. Delete `.railway-secrets` after setup.
