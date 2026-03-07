#!/usr/bin/env python3
"""Add API-based validation fallback when chat page/auth markers fail after login.
Run on VPS: python3 engageflow-login-api-fallback.patch.py
"""
ENGINE = "/root/.openclaw/workspace-margarita/engageflow/backend/automation/engine.py"
SKOOL_AUTH_CHECK_URL = "https://api2.skool.com/self/groups?offset=0&limit=1&prefs=false&members=true"


def _validate_cookies_via_api(cookie_json: str) -> bool:
    """Validate cookie_json via Skool API. Returns True if 2xx."""
    if not cookie_json or not str(cookie_json).strip():
        return False
    try:
        c = json.loads(cookie_json) if isinstance(cookie_json, str) else cookie_json
        arr = c if isinstance(c, list) else [c]
        cookie_header = "; ".join(
            str(x.get("name", "")) + "=" + str(x.get("value", ""))
            for x in arr
            if x.get("name")
        )
        if not cookie_header:
            return False
        headers = {
            "Cookie": cookie_header,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://www.skool.com",
            "Referer": "https://www.skool.com/",
        }
        resp = requests.get(SKOOL_AUTH_CHECK_URL, headers=headers, timeout=12)
        return 200 <= resp.status_code < 300
    except Exception:
        return False


def main():
    with open(ENGINE, "r") as f:
        content = f.read()

    # 1. Add helper after LOGGER (before first def)
    old_logger = "LOGGER = logging.getLogger(\"engageflow.automation\")"
    new_logger = """LOGGER = logging.getLogger("engageflow.automation")

SKOOL_AUTH_CHECK_URL = "https://api2.skool.com/self/groups?offset=0&limit=1&prefs=false&members=true"


def _validate_cookies_via_api(cookie_json: str) -> bool:
    \"\"\"Validate cookie_json via Skool API. Returns True if 2xx.\"\"\"
    if not cookie_json or not str(cookie_json).strip():
        return False
    try:
        c = json.loads(cookie_json) if isinstance(cookie_json, str) else cookie_json
        arr = c if isinstance(c, list) else [c]
        cookie_header = "; ".join(
            str(x.get("name", "")) + "=" + str(x.get("value", ""))
            for x in arr
            if x.get("name")
        )
        if not cookie_header:
            return False
        headers = {
            "Cookie": cookie_header,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://www.skool.com",
            "Referer": "https://www.skool.com/",
        }
        resp = requests.get(SKOOL_AUTH_CHECK_URL, headers=headers, timeout=12)
        return 200 <= resp.status_code < 300
    except Exception:
        return False
"""
    if old_logger in content and "_validate_cookies_via_api" not in content:
        content = content.replace(old_logger, new_logger)
        print("Added _validate_cookies_via_api helper")
    elif "_validate_cookies_via_api" in content:
        print("_validate_cookies_via_api already present")
    else:
        print("Logger block not found")
        return

    # 2. Add API fallback before final "Could not validate chat session" return
    old_block = """                        if "/login" in current_url:
                            manager.update_state("logged_out")
                            return {
                                "success": False,
                                "status": "invalid_credentials",
                                "message": "Still on login page after login attempt",
                            }

                        manager.update_state("error")
                        return {
                            "success": False,
                            "status": "network_error",
                            "message": "Could not validate chat session (chat page/auth markers not detected)",
                        }"""
    new_block = """                        if "/login" in current_url:
                            manager.update_state("logged_out")
                            return {
                                "success": False,
                                "status": "invalid_credentials",
                                "message": "Still on login page after login attempt",
                            }

                        # API fallback: when chat markers fail, validate cookies via Skool API
                        cookie_json = manager.get_cookies_json()
                        if cookie_json and _validate_cookies_via_api(cookie_json):
                            manager.update_state("ready")
                            return {"success": True, "status": "ready", "message": "Session is active", "cookie_json": cookie_json}

                        manager.update_state("error")
                        return {
                            "success": False,
                            "status": "network_error",
                            "message": "Could not validate chat session (chat page/auth markers not detected)",
                        }"""
    if old_block in content:
        content = content.replace(old_block, new_block)
        print("Added API fallback in check_login")
    else:
        print("check_login block not found (may already be patched)")

    # 3. Add same fallback in run_profile_login_refresh_sync
    old_refresh = """                if "/login" in current_url:
                    manager.update_state("logged_out")
                    return {"success": False, "status": "invalid_credentials", "message": "Still on login page after login attempt"}
                manager.update_state("error")
                return {"success": False, "status": "network_error", "message": "Could not validate session"}"""
    new_refresh = """                if "/login" in current_url:
                    manager.update_state("logged_out")
                    return {"success": False, "status": "invalid_credentials", "message": "Still on login page after login attempt"}
                # API fallback: when chat markers fail, validate cookies via Skool API
                cookie_json = manager.get_cookies_json()
                if cookie_json and _validate_cookies_via_api(cookie_json):
                    manager.update_state("ready")
                    if cookie_json:
                        self._save_profile_cookie_json(profile_id, cookie_json)
                    return {"success": True, "status": "ready", "message": "Session is active", "cookie_json": cookie_json}
                manager.update_state("error")
                return {"success": False, "status": "network_error", "message": "Could not validate session"}"""
    if old_refresh in content:
        content = content.replace(old_refresh, new_refresh)
        print("Added API fallback in run_profile_login_refresh_sync")
    else:
        print("run_profile_login_refresh_sync block not found (optional)")

    with open(ENGINE, "w") as f:
        f.write(content)
    print("Patch applied successfully")


if __name__ == "__main__":
    main()
