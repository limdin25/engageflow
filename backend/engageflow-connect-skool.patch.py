#!/usr/bin/env python3
"""Patch EngageFlow app.py: add POST /connect-skool for micro-worker connect flow.
Run on VPS: python3 engageflow-connect-skool.patch.py
"""
import sys
APP = "/root/.openclaw/workspace-margarita/engageflow/backend/app.py"

def main():
    with open(APP, "r") as f:
        content = f.read()

    # 1. Add source and connected_at to ProfileModel
    old_pm = """class ProfileModel(BaseModel):
    id: str
    name: str
    password: Optional[str] = None
    email: Optional[str]
    proxy: Optional[str]
    avatar: str
    status: str
    dailyUsage: int
    groupsConnected: int
    hasPassword: bool = False
    proxyStatus: Optional[str] = None"""
    new_pm = """class ProfileModel(BaseModel):
    id: str
    name: str
    password: Optional[str] = None
    email: Optional[str]
    proxy: Optional[str]
    avatar: str
    status: str
    dailyUsage: int
    groupsConnected: int
    hasPassword: bool = False
    proxyStatus: Optional[str] = None
    source: Optional[str] = None
    connected_at: Optional[str] = None"""
    if old_pm in content:
        content = content.replace(old_pm, new_pm)
        print("Added source, connected_at to ProfileModel")
    elif "source: Optional[str] = None" in content and "connected_at: Optional[str] = None" in content:
        print("ProfileModel already has source/connected_at, skipping")
    else:
        print("ProfileModel block not found")
        sys.exit(1)

    # 2. Update build_profile_model to include source, connected_at
    old_bpm = """    return ProfileModel(
        id=data["id"],
        name=data["name"],
        password=decrypt_secret(data.get("password")),
        email=data["email"],
        proxy=data["proxy"],
        avatar=data["avatar"],
        status=data["status"],
        dailyUsage=data["dailyUsage"],
        groupsConnected=groups_connected,
        hasPassword=bool(str(data.get("password") or "").strip()),
        proxyStatus=proxy_status,
    )"""
    new_bpm = """    return ProfileModel(
        id=data["id"],
        name=data["name"],
        password=decrypt_secret(data.get("password")),
        email=data["email"],
        proxy=data["proxy"],
        avatar=data["avatar"],
        status=data["status"],
        dailyUsage=data["dailyUsage"],
        groupsConnected=groups_connected,
        hasPassword=bool(str(data.get("password") or "").strip()),
        proxyStatus=proxy_status,
        source=data.get("source"),
        connected_at=data.get("connected_at"),
    )"""
    if old_bpm in content and "source=data.get" not in content:
        content = content.replace(old_bpm, new_bpm)
        print("Updated build_profile_model")

    # 3. Add ConnectSkoolModel after ProfileUpdateModel
    if "class ConnectSkoolModel" not in content:
        content = content.replace(
            """class ProfileUpdateModel(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    proxy: Optional[str] = None
    avatar: Optional[str] = None
    status: Optional[str] = None
    dailyUsage: Optional[int] = None
    groupsConnected: Optional[int] = None


class CommunityModel(BaseModel):""",
            """class ProfileUpdateModel(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    proxy: Optional[str] = None
    avatar: Optional[str] = None
    status: Optional[str] = None
    dailyUsage: Optional[int] = None
    groupsConnected: Optional[int] = None


class ConnectSkoolModel(BaseModel):
    email: str
    password: str


class CommunityModel(BaseModel):""",
        )
        print("Added ConnectSkoolModel")

    # 4. Add connect-skool endpoint
    if '"/connect-skool"' in content:
        print("connect-skool endpoint already exists, skipping")
    else:
        old = """    return build_profile_model(row)


@app.put("/profiles/{profile_id}", response_model=ProfileModel)
def update_profile(profile_id: str, payload: ProfileUpdateModel):"""
        new = """    return build_profile_model(row)


@app.post("/connect-skool")
async def connect_skool(payload: ConnectSkoolModel, request: Request):
    \"\"\"Public endpoint for micro-workers to connect Skool accounts. Creates profile with source='micro', status='paused'.\"\"\"
    email = (payload.email or "").strip()
    password_plain = (payload.password or "").strip()
    if not email or not password_plain:
        raise HTTPException(400, "email and password are required")
    profile_id = str(uuid.uuid4())
    password_encrypted = encrypt_secret(password_plain)
    name = email.split("@")[0] or email
    username = email
    avatar = "".join([part[0] for part in name.split() if part]).upper()[:2] or "NA"
    connected_at = datetime.now(timezone.utc).isoformat()
    with get_db() as db:
        db.execute(
            "INSERT INTO profiles (id, name, username, password, email, proxy, avatar, status, dailyUsage, groupsConnected, source, connected_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (profile_id, name, username, password_encrypted, email, None, avatar, "paused", 0, 0, "micro", connected_at),
        )
        db.commit()
    engine = get_automation_engine(request)
    try:
        result = await engine.check_login(profile_id)
        if isinstance(result, dict) and result.get("success"):
            return {"success": True, "profileId": profile_id, "message": "Connected"}
        msg = str(result.get("message", "Login failed")) if isinstance(result, dict) else "Login failed"
        with get_db() as db:
            db.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
            db.commit()
        raise HTTPException(400, msg)
    except HTTPException:
        raise
    except Exception as e:
        with get_db() as db:
            db.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
            db.commit()
        raise HTTPException(400, str(e))


@app.put("/profiles/{profile_id}", response_model=ProfileModel)
def update_profile(profile_id: str, payload: ProfileUpdateModel):"""
        if old not in content:
            print("Could not find insertion point for connect-skool endpoint")
            sys.exit(1)
        content = content.replace(old, new)
        print("Added POST /connect-skool endpoint")

    with open(APP, "w") as f:
        f.write(content)
    print("Patch applied successfully")


if __name__ == "__main__":
    main()
