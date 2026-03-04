# Railway Secrets — Add to GitHub

**One-time setup.** Add these to GitHub repo → Settings → Secrets and variables → Actions:

| Secret Name         | Value |
|---------------------|-------|
| RAILWAY_TOKEN       | `8ba7616a-c9e4-4982-9d92-abd7cc44ed7f` (dev) — **rotate after setup** |
| RAILWAY_PROJECT_ID  | `f2cddd1a-3d44-47f6-bd18-5ce566b88da4` |

1. New repository secret → Name: `RAILWAY_TOKEN` → Value: `8ba7616a-c9e4-4982-9d92-abd7cc44ed7f`
2. New repository secret → Name: `RAILWAY_PROJECT_ID` → Value: `f2cddd1a-3d44-47f6-bd18-5ce566b88da4`

**Rotate tokens later** in Railway → Settings → Tokens, then update GitHub Secrets. Delete this file or remove token from it after setup.
