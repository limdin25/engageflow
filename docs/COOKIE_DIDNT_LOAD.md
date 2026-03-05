# Cookie didn’t load for an account (e.g. marknoah2024@gmail.com)

## What “cookie didn’t load” means

- The **Joiner** app shows auth status per account. If you see **Missing Cookies** or **No cookies** for an account (e.g. `marknoah2024@gmail.com`), it means that account’s **cookie** has not been stored in the database yet (or failed to load when you expected it).
- Cookies are stored in the shared **profiles** table in the `cookie_json` column. Joiner and EngageFlow use the same DB on Railway (`/data/engageflow.db`), so once `cookie_json` is set for a profile, both apps see it.

## Why it might not load

1. **Never added** — Cookies were never added for that profile in Joiner (Connect or Paste cookies).
2. **Sync didn’t bring it** — “Sync cookies” only **copies from EngageFlow → Joiner** when EngageFlow already has a cookie for that profile. If EngageFlow never had the cookie, sync won’t create it.
3. **Wrong profile** — The email you’re looking at might be a different profile id than the one you added cookies for (e.g. duplicate email in another row).
4. **Paste/Connect failed** — You pasted or clicked Connect but the request failed (network, validation, or auth). Check Joiner UI for an error message and try again.

## How to fix it

### In the Joiner UI (joiner-dev.up.railway.app)

1. Open **Accounts** and find the account (e.g. `marknoah2024@gmail.com`).
2. **Option A — Paste cookies**
   - Export cookies from the browser where you’re logged into Skool (e.g. Cookie-Editor extension → Export as JSON array).
   - Click **Paste Cookies** for that account, paste the JSON (or `name=value; name2=value2`), submit.
   - If validation succeeds, the UI will show “Cookies validated and stored” and the account will show **Connected**.
3. **Option B — Connect (Skool password)**
   - Click **Connect** for that account and enter the Skool password when prompted.
   - Joiner will log in with Playwright and store cookies. If it succeeds, the account will show **Connected**.

### If you expect cookies to come from EngageFlow

- Run **cookie sync** so Joiner pulls cookies from EngageFlow:  
  `POST /internal/joiner/sync-cookies` with header `X-JOINER-SECRET: <ENGAGEFLOW_JOINER_SECRET>` (e.g. from Railway Joiner service).
- Sync only **fills in** profiles where EngageFlow has `cookie_json` and Joiner doesn’t. So Ensure the profile has cookies set in EngageFlow first (e.g. via whatever flow writes `cookie_json` there), then trigger sync.

### After adding cookies

- The list refreshes every few seconds. If it still shows **Missing Cookies**, do a hard refresh (or wait for the next poll). Confirm you’re on the same profile row (same email and id) where you pasted/connected.

## Quick check

- In Joiner, open the account row and expand it. Under **Cookies**, click **Reveal**: it should say “Cookies present (hidden for security)” after a successful paste/connect. If it still says “No cookies”, add cookies again (Paste or Connect) for that exact profile.
