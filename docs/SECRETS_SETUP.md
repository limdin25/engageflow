# Railway Secrets — Add to GitHub

**One-time setup.** Add these to GitHub repo → Settings → Secrets and variables → Actions.

**Project:** efficient-ambition | **Project ID:** `f2cddd1a-3d44-47f6-bd18-5ce566b88da4`

| Secret | Value | Purpose |
|--------|-------|---------|
| RAILWAY_TOKEN | from .railway-secrets | DEV project token (push to dev) |
| RAILWAY_TOKEN_PROD | from .railway-secrets | Production project token (push to main) |
| RAILWAY_PROJECT_ID | `f2cddd1a-3d44-47f6-bd18-5ce566b88da4` | Project ID |
| RAILWAY_API_TOKEN | from Railway → Account Settings → Tokens | Account token for `railway link` in CI |

**Rotate tokens later** in Railway → Settings → Tokens, then update GitHub Secrets. Delete `.railway-secrets` after setup.
