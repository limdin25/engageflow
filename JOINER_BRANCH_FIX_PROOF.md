# Joiner Railway Branch Fix + Proof

## Task (Railway UI — Manual)

1. Open Railway project
2. Select **Joiner** service
3. **Settings** → **Source**
4. Change **Branch** from `main` → `dev`
5. Save, then **Redeploy** (disable build cache if available)

---

## Proof (Run After Redeploy)

### A) Sync endpoint (200 expected)

```bash
curl -sS -X POST -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET" \
  https://joiner-dev.up.railway.app/internal/joiner/sync-cookies | jq .
```

**Expected:** `{ "success": true, "scanned": 3, "updated": N }`

**Current (before fix):** 404

---

### B) Profiles endpoint

```bash
curl -sS https://joiner-dev.up.railway.app/api/profiles | jq '.[] | {email, has_cookie_json:(.has_cookie_json // (.cookie_json!=null)), auth_status}'
```

**Current state:**
| email | has_cookie_json | auth_status |
|-------|-----------------|-------------|
| hugords100+1@gmail.com | true | connected |
| hugords100@gmail.com | false | disconnected |
| marknoah2024@gmail.com | false | disconnected |

---

## Output Template (Fill After Fix)

### 1) Joiner Source branch

- [ ] Branch set to `dev` (screenshot or note)

### 2) Deploy log

- [ ] Build from dev (commit 27f95a7 or 9baef8c+)

### 3) Curl proof

**A) Sync:**
```
(paste output)
```

**B) Profiles:**
```
(paste output)
```

---

## Stop Condition

If sync still 404 after branch switch: capture Railway build/deploy logs and report why it didn’t redeploy from dev.
