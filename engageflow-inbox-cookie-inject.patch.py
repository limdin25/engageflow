#!/usr/bin/env python3
"""Inject cookie_json from DB into inbox sync so Playwright uses fresh Skool session."""
import re

APP = "/root/.openclaw/workspace-margarita/engageflow/backend/app.py"


def main():
    with open(APP, "r") as f:
        c = f.read()

    # 1. Add cookie_json to profile SELECT in sync
    old_select = """    profile_rows = db.execute(
        \"\"\"
        SELECT id, name, proxy, email
        FROM profiles
        WHERE lower(trim(coalesce(status, ''))) IN ('ready', 'running')
        ORDER BY name
        \"\"\"
    ).fetchall()"""
    new_select = """    profile_rows = db.execute(
        \"\"\"
        SELECT id, name, proxy, email, cookie_json
        FROM profiles
        WHERE lower(trim(coalesce(status, ''))) IN ('ready', 'running')
        ORDER BY name
        \"\"\"
    ).fetchall()"""
    if new_select not in c:
        c = c.replace(old_select, new_select)
        print("Added cookie_json to profile SELECT")

    # 2. Pass cookie_json to fetch
    old_call = """                    profile_cards, sync_error = _fetch_live_skool_chat_cards_with_timeout(
                        profile_id=profile_id,
                        profile_name=profile_name,
                        proxy=profile_row["proxy"],
                        expected_identities=[str(profile_row["name"] or ""), str(profile_row["email"] or "")],
                        known_profile_slugs=known_profile_slugs,
                        cached_cards_by_chat=cached_cards_by_chat,
                    )"""
    new_call = """                    profile_cards, sync_error = _fetch_live_skool_chat_cards_with_timeout(
                        profile_id=profile_id,
                        profile_name=profile_name,
                        proxy=profile_row["proxy"],
                        expected_identities=[str(profile_row["name"] or ""), str(profile_row["email"] or "")],
                        known_profile_slugs=known_profile_slugs,
                        cached_cards_by_chat=cached_cards_by_chat,
                        cookie_json=(str(profile_row["cookie_json"] or "").strip() or None),
                    )"""
    if "cookie_json=(profile_row.get" not in c:
        c = c.replace(old_call, new_call)
        print("Added cookie_json to fetch call")

    # 3. Add cookie_json to _fetch_live_skool_chat_cards_with_timeout
    c = c.replace(
        "cached_cards_by_chat: Optional[Dict[str, Dict[str, Any]]] = None,\n    timeout_seconds: int = SKOOL_CHAT_PROFILE_SYNC_TIMEOUT_SECONDS,",
        "cached_cards_by_chat: Optional[Dict[str, Dict[str, Any]]] = None,\n    cookie_json: Optional[str] = None,\n    timeout_seconds: int = SKOOL_CHAT_PROFILE_SYNC_TIMEOUT_SECONDS,",
    )
    if "cookie_json: Optional[str] = None," in c:
        print("Added cookie_json param to with_timeout")

    # 4. Pass cookie_json in the inner call (positional)
    old_inner = """        return _fetch_live_skool_chat_cards(
            profile_id,
            profile_name,
            proxy,
            expected_identities,
            known_profile_slugs,
            cached_cards_by_chat,
        )"""
    new_inner = """        return _fetch_live_skool_chat_cards(
            profile_id,
            profile_name,
            proxy,
            expected_identities,
            known_profile_slugs,
            cached_cards_by_chat,
            cookie_json,
        )"""
    if old_inner in c:
        c = c.replace(old_inner, new_inner)
        print("Added cookie_json to inner fetch call")

    # 5. Add cookie_json to _fetch_live_skool_chat_cards signature
    old_fetch_sig = """def _fetch_live_skool_chat_cards(
    profile_id: str,
    profile_name: str,
    proxy: Optional[str],
    expected_identities: Optional[List[str]] = None,
    known_profile_slugs: Optional[Set[str]] = None,
    cached_cards_by_chat: Optional[Dict[str, Dict[str, Any]]] = None,
) -> tuple[List[Dict[str, Any]], Optional[str]]:"""
    new_fetch_sig = """def _fetch_live_skool_chat_cards(
    profile_id: str,
    profile_name: str,
    proxy: Optional[str],
    expected_identities: Optional[List[str]] = None,
    known_profile_slugs: Optional[Set[str]] = None,
    cached_cards_by_chat: Optional[Dict[str, Dict[str, Any]]] = None,
    cookie_json: Optional[str] = None,
) -> tuple[List[Dict[str, Any]], Optional[str]]:"""
    if "cookie_json: Optional[str] = None," not in c or "def _fetch_live_skool_chat_cards" in c:
        c = c.replace(old_fetch_sig, new_fetch_sig)
        print("Added cookie_json param to _fetch_live_skool_chat_cards")

    # 6. Inject cookies before _goto_skool_entry_page - find the block and add cookie injection
    inject_block = '''
                    # Inject cookies from DB if available (ensures fresh Skool session)
                    if cookie_json and cookie_json.strip():
                        try:
                            import json as _json
                            arr = _json.loads(cookie_json) if isinstance(cookie_json, str) else cookie_json
                            if isinstance(arr, dict):
                                arr = [arr]
                            pw_cookies = []
                            for x in (arr or []):
                                name = x.get("name") or x.get("key")
                                value = str(x.get("value", ""))
                                if name:
                                    pw_cookies.append({
                                        "name": str(name),
                                        "value": value,
                                        "domain": ".skool.com",
                                        "path": "/",
                                    })
                            if pw_cookies:
                                page.goto("https://www.skool.com/", wait_until="domcontentloaded", timeout=15000)
                                context.add_cookies(pw_cookies)
                        except Exception as _cookie_exc:
                            LOGGER.warning("Inbox sync cookie inject failed for %s: %s", profile_id, _cookie_exc)
'''
    # Find: page = context.pages[0]... then page_ready = False, try: nav_ok, _ = _goto_skool_entry_page
    old_nav = """                    page = context.pages[0] if context.pages else context.new_page()
                    page.set_default_timeout(12000)
                    page_ready = False
                    try:
                        nav_ok, _ = _goto_skool_entry_page(page, nav_timeout_ms)"""
    new_nav = """                    page = context.pages[0] if context.pages else context.new_page()
                    page.set_default_timeout(12000)
                    page_ready = False
                    try:""" + inject_block + """
                        nav_ok, _ = _goto_skool_entry_page(page, nav_timeout_ms)"""
    if inject_block.strip() not in c:
        c = c.replace(old_nav, new_nav)
        print("Added cookie injection before navigation")

    with open(APP, "w") as f:
        f.write(c)
    print("Patch applied")


if __name__ == "__main__":
    main()
