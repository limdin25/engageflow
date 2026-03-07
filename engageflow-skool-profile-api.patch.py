#!/usr/bin/env python3
"""Add PATCH /profiles/{id}/skool-profile and POST /profiles/{id}/skool-profile/photo.
Uses Skool API (api2.skool.com) with profile cookies. Run on VPS.
"""
import os
import sys
APP = "/root/.openclaw/workspace-margarita/engageflow/backend/app.py"

SKOOL_PROFILE_UPDATE = '''
class SkoolProfileUpdateModel(BaseModel):
    bio: Optional[str] = None
    location: Optional[str] = None
    socialLinks: Optional[Dict[str, str]] = None


def _skool_api_request(profile_id: str, method: str, path: str, body=None, content_type: str = "application/json", files=None):
    """Call Skool API with profile cookies. Returns (ok: bool, data: dict, message: str)."""
    auth = ensure_profile_auth(profile_id)
    if not auth.get("ok") or not auth.get("cookie_json"):
        return False, None, auth.get("message", "Not logged in") or "No cookies"
    cookies = _cookies_from_json(auth["cookie_json"])
    if not cookies:
        return False, None, "No cookies"
    headers = {
        "Cookie": cookies,
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://www.skool.com",
        "Referer": "https://www.skool.com/",
    }
    if content_type and not files:
        headers["Content-Type"] = content_type
    url = f"https://api2.skool.com{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers=headers, timeout=15)
        elif method == "PUT":
            r = requests.put(url, headers=headers, json=body, timeout=15)
        elif method == "POST" and files:
            headers.pop("Content-Type", None)
            r = requests.post(url, headers=headers, files=files, timeout=30)
        else:
            r = requests.put(url, headers=headers, json=body, timeout=15)
        if r.status_code in (401, 403):
            return False, None, "Session expired or invalid"
        data = r.json() if r.text else {}
        return 200 <= r.status_code < 300, data, "" if r.ok else (data.get("message") or r.text[:200])
    except Exception as e:
        return False, None, str(e)[:200]


def _skool_get_user_id(profile_id: str) -> Optional[str]:
    """Get Skool user id from /self/profile."""
    ok, data, _ = _skool_api_request(profile_id, "GET", "/self/profile")
    if not ok or not data:
        return None
    uid = data.get("id") or data.get("user", {}).get("id") or data.get("userId")
    return str(uid) if uid else None


@app.patch("/profiles/{profile_id}/skool-profile")
def update_skool_profile(profile_id: str, payload: SkoolProfileUpdateModel):
    """Update Skool profile (bio, location, social links) via Skool API."""
    with get_db() as db:
        if not db.execute("SELECT id FROM profiles WHERE id = ?", (profile_id,)).fetchone():
            raise HTTPException(404, "Profile not found")
    user_id = _skool_get_user_id(profile_id)
    if not user_id:
        raise HTTPException(400, "Could not get Skool user (session may be expired)")
    updated = []
    if payload.bio is not None:
        ok, _, msg = _skool_api_request(profile_id, "PUT", f"/users/{user_id}/metadata/bio", {"value": payload.bio[:150]})
        if not ok:
            raise HTTPException(400, msg or "Failed to update bio")
        updated.append("bio")
    if payload.location is not None:
        ok, _, msg = _skool_api_request(profile_id, "PUT", f"/users/{user_id}/metadata/location", {"value": payload.location})
        if not ok:
            raise HTTPException(400, msg or "Failed to update location")
        updated.append("location")
    if payload.socialLinks:
        for key, url in payload.socialLinks.items():
            if url is None or str(url).strip() == "":
                continue
            field = {"website": "link_website", "instagram": "link_instagram", "x": "link_twitter",
                     "youtube": "link_youtube", "linkedin": "link_linkedin", "facebook": "link_facebook"}.get(key.lower(), key)
            ok, _, msg = _skool_api_request(profile_id, "PUT", f"/users/{user_id}/metadata/{field}", {"value": str(url).strip()})
            if not ok:
                raise HTTPException(400, msg or f"Failed to update {key}")
            updated.append(key)
    return {"success": True, "updated": updated}


@app.post("/profiles/{profile_id}/skool-profile/photo")
async def update_skool_profile_photo(profile_id: str, photo: "UploadFile" = None):
    """Upload profile photo to Skool. Requires multipart/form-data with 'photo' file."""
    from fastapi import File, UploadFile
    if not photo or not photo.filename:
        raise HTTPException(400, "Photo file required")
    with get_db() as db:
        if not db.execute("SELECT id FROM profiles WHERE id = ?", (profile_id,)).fetchone():
            raise HTTPException(404, "Profile not found")
    user_id = _skool_get_user_id(profile_id)
    if not user_id:
        raise HTTPException(400, "Could not get Skool user (session may be expired)")
    content = await photo.read()
    if not content or len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large or empty (max 10MB)")
    files = {"file": (photo.filename, content, photo.content_type or "image/jpeg")}
    ok, data, msg = _skool_api_request(profile_id, "POST", f"/users/{user_id}/avatar", body=None, content_type=None, files=files)
    if not ok:
        raise HTTPException(400, msg or "Failed to upload photo")
    return {"success": True, "message": "Photo updated"}
'''

def main():
    with open(APP, "r") as f:
        content = f.read()

    if "SkoolProfileUpdateModel" in content:
        print("Skool profile API already present")
        return

    # Ensure Dict is imported for SkoolProfileUpdateModel.socialLinks
    if "from typing import" in content and "Dict" not in content:
        content = content.replace("from typing import Optional", "from typing import Dict, Optional", 1)
        if "Dict" not in content:
            content = content.replace("from typing import ", "from typing import Dict, ", 1)
        print("Added Dict to typing imports")

    # Add import for File, UploadFile
    if "from fastapi import" in content and "UploadFile" not in content:
        content = content.replace(
            "from fastapi import FastAPI, HTTPException, Request",
            "from fastapi import FastAPI, File, HTTPException, Request, UploadFile",
        )
        print("Added UploadFile import")

    # Add model and endpoints - after ConnectSkoolModel
    if "class ConnectSkoolModel" in content:
        insert_after = "class ConnectSkoolModel(BaseModel):\n    email: str\n    password: str\n\n\nclass CommunityModel"
        insert_block = "class ConnectSkoolModel(BaseModel):\n    email: str\n    password: str\n\n\nclass SkoolProfileUpdateModel(BaseModel):\n    bio: Optional[str] = None\n    location: Optional[str] = None\n    socialLinks: Optional[Dict[str, str]] = None\n\n\nclass CommunityModel"
        if insert_block not in content:
            content = content.replace(insert_after, insert_block)
            print("Added SkoolProfileUpdateModel")
    else:
        print("ConnectSkoolModel not found")
        return

    # Insert the skool-profile endpoints after reset_profile_counters and before delete_profile.
    # Try multiple anchor patterns (db.commit vs _db_commit_with_retry).
    INSERT_BLOCK = """

def _skool_api_request(profile_id: str, method: str, path: str, body=None, content_type: str = "application/json", files=None):
    \"\"\"Call Skool API with profile cookies. Returns (ok: bool, data: dict, message: str).\"\"\"
    auth = ensure_profile_auth(profile_id)
    if not auth.get("ok") or not auth.get("cookie_json"):
        return False, None, auth.get("message", "Not logged in") or "No cookies"
    cookies = _cookies_from_json(auth["cookie_json"])
    if not cookies:
        return False, None, "No cookies"
    headers = {
        "Cookie": cookies,
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://www.skool.com",
        "Referer": "https://www.skool.com/",
    }
    if content_type and not files:
        headers["Content-Type"] = content_type
    url = f"https://api2.skool.com{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers=headers, timeout=15)
        elif method == "PUT":
            r = requests.put(url, headers=headers, json=body, timeout=15)
        elif method == "POST" and files:
            headers.pop("Content-Type", None)
            r = requests.post(url, headers=headers, files=files, timeout=30)
        else:
            r = requests.put(url, headers=headers, json=body, timeout=15)
        if r.status_code in (401, 403):
            return False, None, "Session expired or invalid"
        data = r.json() if r.text else {}
        return 200 <= r.status_code < 300, data, "" if r.ok else (data.get("message") or r.text[:200])
    except Exception as e:
        return False, None, str(e)[:200]


def _skool_get_user_id(profile_id: str) -> Optional[str]:
    \"\"\"Get Skool user id from /self/profile.\"\"\"
    ok, data, _ = _skool_api_request(profile_id, "GET", "/self/profile")
    if not ok or not data:
        return None
    uid = data.get("id") or (data.get("user", {}) or {}).get("id") or data.get("userId")
    return str(uid) if uid else None


@app.patch("/profiles/{profile_id}/skool-profile")
def update_skool_profile(profile_id: str, payload: SkoolProfileUpdateModel):
    \"\"\"Update Skool profile (bio, location, social links) via Skool API.\"\"\"
    with get_db() as db:
        if not db.execute("SELECT id FROM profiles WHERE id = ?", (profile_id,)).fetchone():
            raise HTTPException(404, "Profile not found")
    user_id = _skool_get_user_id(profile_id)
    if not user_id:
        raise HTTPException(400, "Could not get Skool user (session may be expired)")
    updated = []
    if payload.bio is not None:
        ok, _, msg = _skool_api_request(profile_id, "PUT", f"/users/{user_id}/metadata/bio", {"value": (payload.bio or "")[:150]})
        if not ok:
            raise HTTPException(400, msg or "Failed to update bio")
        updated.append("bio")
    if payload.location is not None:
        ok, _, msg = _skool_api_request(profile_id, "PUT", f"/users/{user_id}/metadata/location", {"value": payload.location or ""})
        if not ok:
            raise HTTPException(400, msg or "Failed to update location")
        updated.append("location")
    if payload.socialLinks:
        field_map = {"website": "link_website", "instagram": "link_instagram", "x": "link_twitter",
                     "youtube": "link_youtube", "linkedin": "link_linkedin", "facebook": "link_facebook"}
        for key, url in payload.socialLinks.items():
            if url is None or str(url).strip() == "":
                continue
            field = field_map.get(str(key).lower(), key)
            ok, _, msg = _skool_api_request(profile_id, "PUT", f"/users/{user_id}/metadata/{field}", {"value": str(url).strip()})
            if not ok:
                raise HTTPException(400, msg or f"Failed to update {key}")
            updated.append(key)
    return {"success": True, "updated": updated}


@app.post("/profiles/{profile_id}/skool-profile/photo")
async def update_skool_profile_photo(profile_id: str, photo: UploadFile = File(...)):
    \"\"\"Upload profile photo to Skool. Requires multipart/form-data with 'photo' file.\"\"\"
    with get_db() as db:
        if not db.execute("SELECT id FROM profiles WHERE id = ?", (profile_id,)).fetchone():
            raise HTTPException(404, "Profile not found")
    user_id = _skool_get_user_id(profile_id)
    if not user_id:
        raise HTTPException(400, "Could not get Skool user (session may be expired)")
    content = await photo.read()
    if not content or len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large or empty (max 10MB)")
    files = {"file": (photo.filename or "photo.jpg", content, photo.content_type or "image/jpeg")}
    ok, data, msg = _skool_api_request(profile_id, "POST", f"/users/{user_id}/avatar", body=None, content_type=None, files=files)
    if not ok:
        raise HTTPException(400, msg or "Failed to upload photo")
    return {"success": True, "message": "Photo updated"}


@app.delete("/profiles/{profile_id}")
def delete_profile(profile_id: str):"""

    # Try anchor 1: _db_commit_with_retry
    old_block_1 = """        _db_commit_with_retry(db)
    return {"success": True}


@app.delete("/profiles/{profile_id}")
def delete_profile(profile_id: str):"""
    # Try anchor 2: db.commit
    old_block_2 = """        db.commit()
    return {"success": True}


@app.delete("/profiles/{profile_id}")
def delete_profile(profile_id: str):"""

    inserted = False
    for old_block in (old_block_1, old_block_2):
        if old_block in content:
            # Insert INSERT_BLOCK between reset_profile_counters return and delete_profile
            new_block = old_block.replace(
                "\n\n@app.delete(\"/profiles/{profile_id}\")\ndef delete_profile(profile_id: str):",
                "\n" + INSERT_BLOCK + "\n\n@app.delete(\"/profiles/{profile_id}\")\ndef delete_profile(profile_id: str):",
            )
            content = content.replace(old_block, new_block)
            inserted = True
            print("Added skool-profile endpoints")
            break
    if not inserted:
        print("Insert block not found (tried _db_commit_with_retry and db.commit anchors)")
        sys.exit(1)

    # Ensure File is imported for UploadFile/File(...)
    if "File(" not in content and "UploadFile" in content:
        # Check if File is imported
        if "from fastapi import" in content and "File" not in content:
            content = content.replace(
                "from fastapi import FastAPI, File, HTTPException, Request, UploadFile",
                "from fastapi import FastAPI, File, HTTPException, Request, UploadFile",
            )
    # File is used as File(...) - need to ensure it's imported
    if "File(...)" in content and "File," not in content:
        content = content.replace(
            "from fastapi import FastAPI, HTTPException, Request",
            "from fastapi import FastAPI, File, HTTPException, Request, UploadFile",
        )

    with open(APP, "w") as f:
        f.write(content)
    print("Patch applied successfully")


if __name__ == "__main__":
    main()
