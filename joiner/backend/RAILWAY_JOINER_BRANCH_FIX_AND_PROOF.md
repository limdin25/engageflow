# Joiner: Fix Railway Source Branch → dev, Then Prove Live

**Cursor cannot open the Railway dashboard.** Steps 1–3 must be done by someone with Railway access. Steps 4–6 (live proofs) can be run by Cursor after the fix.

---

## 1) Railway UI (you must do this)

1. Open **Railway** → project **efficient-ambition** → service **Joiner**.
2. Go to **Settings** → **Source**.
3. Set exactly:
   - **Branch:** `dev`
   - **Root Directory:** `joiner/backend`
   - (Repo should be `limdin25/engageflow`, Build: Dockerfile)
4. **Save**.

**Proof to capture:** Screenshot or exact text from the Source panel showing **Branch = dev** and **Root Directory = joiner/backend**.

---

## 2) Force a real rebuild from source

- In Joiner: **Deployments** → **Deploy latest commit** (or **Redeploy**).
- If you see **Disable build cache**, use it so the build checks out dev and includes commit 98dc055 (or newer).

---

## 3) Build log proof

- **Joiner** → **Deployments** → latest deployment → **Build Logs**.
- Copy a short excerpt that shows:
  - branch **dev** checked out
  - commit SHA built (98dc055 or d8e9111 or newer)
  - build context **joiner/backend**

Paste that excerpt into the proof bundle below.

---

## 4) Live proof A — fingerprint header

```bash
curl -i https://joiner-dev.up.railway.app/
```

**Required:** Response must include header **X-Joiner-Git-Sha:** with a value (e.g. `98dc055` or `unknown`).  
If this header is missing, the service is still on the old build; do not claim success.

---

## 5) Live proof B — db-info route

```bash
curl -sS "https://joiner-dev.up.railway.app/internal/joiner/debug/db-info" \
  -H "X-JOINER-SECRET: $ENGAGEFLOW_JOINER_SECRET"
```

**Required:** Response must be **JSON** (not 404) and include **profiles_has_cookie_json: true** (and **profiles_columns** including **cookie_json**).  
Redact the secret in any pasted output.

---

## 6) Live proof C — auth codes (no-cookie profile)

**No-cookie profile id:** `aa599316-f52c-4428-94df-4d101078c765`

```bash
curl -sS "https://joiner-dev.up.railway.app/api/profiles/aa599316-f52c-4428-94df-4d101078c765/skool-auth"
```

**Required:** Response must include **"code":"NO_COOKIE_JSON"** (or **EMPTY_COOKIE_LIST**).  
Do not claim success without this.

---

## 7) Proof bundle (fill after fix)

| # | Item | Your proof |
|---|------|------------|
| 1 | Source settings | Screenshot or exact text: Branch=dev, Root Directory=joiner/backend |
| 2 | Build log | Short excerpt: branch dev, commit sha, joiner/backend context |
| 3 | curl -i / | Full output showing **X-Joiner-Git-Sha** header |
| 4 | db-info | JSON (redacted) with profiles_has_cookie_json: true |
| 5 | skool-auth no-cookie | Output showing "code":"NO_COOKIE_JSON" (or EMPTY_COOKIE_LIST) |

**Do not claim success without all three live proofs (A, B, C) passing.**

---

## Current state (before branch fix)

Running the three proofs **before** setting Branch=dev yields:

- **A)** No X-Joiner-Git-Sha header.
- **B)** 404 on /internal/joiner/debug/db-info.
- **C)** `{"valid":false,"error":"No cookies"}` with no **code** field.

This confirms Joiner is not building from dev until the dashboard source branch is set to **dev** and a rebuild is triggered.
