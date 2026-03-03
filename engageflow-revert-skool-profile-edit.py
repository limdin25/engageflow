#!/usr/bin/env python3
"""Revert Skool profile edit (Phase 2): restore Edit profile to window.open, remove PATCH/POST endpoints."""
import re
import sys

APP = "/root/.openclaw/workspace-margarita/engageflow/backend/app.py"
PAGE = "/root/.openclaw/workspace-margarita/engageflow/frontend/src/pages/ProfilesPage.tsx"
API = "/root/.openclaw/workspace-margarita/engageflow/frontend/src/lib/api.ts"


def revert_backend():
    with open(APP, "r") as f:
        c = f.read()

    # Remove SkoolProfileUpdateModel
    c = re.sub(
        r"\n\nclass SkoolProfileUpdateModel\(BaseModel\):\n    bio: Optional\[str\] = None\n    location: Optional\[str\] = None\n    socialLinks: Optional\[Dict\[str, str\]\] = None\n\n\nclass CommunityModel",
        "\n\nclass CommunityModel",
        c,
    )
    if "SkoolProfileUpdateModel" in c:
        c = c.replace(
            "class SkoolProfileUpdateModel(BaseModel):\n    bio: Optional[str] = None\n    location: Optional[str] = None\n    socialLinks: Optional[Dict[str, str]] = None\n\n\n",
            "",
        )

    # Remove _skool_api_request, _skool_get_user_id, update_skool_profile, update_skool_profile_photo
    # Keep @app.delete("/profiles/{profile_id}")
    pattern = r"\n\ndef _skool_api_request\(.*?\n(?:.*?\n)*?    return \{\"success\": True, \"message\": \"Photo updated\"\}\n\n\n@app\.delete"
    c = re.sub(pattern, "\n\n@app.delete", c, flags=re.DOTALL)
    if "_skool_api_request" in c:
        # Fallback: remove block from def _skool_api_request to @app.delete (exclusive)
        start = c.find("\ndef _skool_api_request(")
        if start >= 0:
            end = c.find("\n@app.delete(\"/profiles/{profile_id}\")", start)
            if end >= 0:
                c = c[:start] + c[end:]

    # Remove File, UploadFile from imports if only used by skool-profile
    if "UploadFile" in c and "File(" not in c:
        c = c.replace("from fastapi import FastAPI, File, HTTPException, Request, UploadFile", "from fastapi import FastAPI, HTTPException, Request")
    elif "File," in c and "UploadFile" in c:
        c = c.replace("from fastapi import FastAPI, File, HTTPException, Request, UploadFile", "from fastapi import FastAPI, HTTPException, Request")

    with open(APP, "w") as f:
        f.write(c)
    print("Backend reverted")


def revert_frontend():
    with open(PAGE, "r") as f:
        c = f.read()

    # Remove edit modal state
    c = c.replace(
        "  const [checkProxyMessage, setCheckProxyMessage] = useState<Record<string, string>>({});\n  const [editModalProfile, setEditModalProfile] = useState<Profile | null>(null);\n  const [editForm, setEditForm] = useState({ bio: \"\", location: \"\", website: \"\", instagram: \"\", x: \"\" });\n  const [editSaving, setEditSaving] = useState(false);\n  const [editError, setEditError] = useState(\"\");\n  const [photoFile, setPhotoFile] = useState<File | null>(null);",
        "  const [checkProxyMessage, setCheckProxyMessage] = useState<Record<string, string>>({});",
    )

    # Replace Edit profile button: setEditModalProfile(selected) -> window.open
    c = c.replace(
        "onClick={() => setEditModalProfile(selected)} className=\"inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-border text-xs font-medium text-foreground hover:bg-muted transition-colors\" title=\"Edit Skool profile\"",
        "onClick={() => window.open('https://www.skool.com/settings?t=profile', '_blank')} className=\"inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-border text-xs font-medium text-foreground hover:bg-muted transition-colors\" title=\"Open Skool profile settings\"",
    )

    # Remove modal block - from {editModalProfile && ( to closing );
    start = c.find("      {editModalProfile && (")
    if start >= 0:
        # Find matching closing - need to match the div structure
        depth = 0
        i = start + len("      {editModalProfile && (")
        in_jsx = True
        while i < len(c):
            if c[i:i+2] == "</":
                # Find end of tag
                j = c.find(">", i) + 1
                if "div" in c[i:j]:
                    depth -= 1
                i = j
                continue
            if c[i:i+2] == "<d":
                j = c.find(">", i) + 1
                if c[i:j].strip().startswith("<div"):
                    depth += 1
                i = j
                continue
            if c[i] == ")" and in_jsx and depth == 0:
                # End of editModalProfile && (...)
                end = c.find("}", i) + 1
                if end > i:
                    c = c[:start] + c[end:]
                    break
            i += 1
            if i > start + 5000:
                break

    # Simpler: remove block by regex
    if "editModalProfile" in c:
        # Match from {editModalProfile && ( to the closing });
        c = re.sub(
            r"\n      \{editModalProfile && \(\n        <div[^>]*>.*?</div>\n      \)\}",
            "",
            c,
            flags=re.DOTALL,
        )
    # Fallback: remove line by line
    if "editModalProfile" in c:
        lines = c.split("\n")
        out = []
        skip = 0
        i = 0
        while i < len(lines):
            if "editModalProfile && (" in lines[i]:
                skip = 1
                depth = 0
                i += 1
                while i < len(lines) and (skip > 0 or depth > 0):
                    if "{" in lines[i] and "editModalProfile" in lines[i]:
                        depth += 1
                    if "}" in lines[i]:
                        depth -= 1
                    if ")}" in lines[i] and depth <= 0:
                        skip = 0
                        i += 1
                        break
                    i += 1
                continue
            i += 1
            if skip == 0:
                out.append(lines[i-1] if i > 0 else "")
        if out:
            c = "\n".join(out)
        else:
            # Manual removal
            c = c.replace("      {editModalProfile && (\n        <div className=\"fixed inset-0 z-50 flex items-center justify-center bg-black/50\" onClick={() => !editSaving && setEditModalProfile(null)}>\n          <div className=\"bg-background rounded-lg shadow-xl max-w-md w-full mx-4 p-6\" onClick={e => e.stopPropagation()}>\n            <h3 className=\"text-lg font-semibold mb-4\">Edit Skool profile</h3>\n", "")
            # Remove rest of modal in chunks
            for pattern in [
                r'<div className="space-y-4">.*?profile photo</label>\n                <input[^>]*/>\n              </div>\n            </div>\n            \{editError[^}]+\}\n            <div className="flex gap-2 mt-6">.*?setEditModalProfile\(null\);\n                  setPhotoFile\(null\);\n                  refreshAll\(\);',
                r'</button>\n            </div>\n          </div>\n        </div>\n      \)}',
            ]:
                c = re.sub(pattern, "", c, flags=re.DOTALL)

    with open(PAGE, "w") as f:
        f.write(c)
    print("ProfilesPage reverted")


def revert_api():
    with open(API, "r") as f:
        c = f.read()

    # Remove profileUpdateSkool and profileUploadSkoolPhoto
    old = """  profileResetCounters: (profileId: string) => request<{ success: boolean }>(`/profiles/${profileId}/reset-counters`, { method: "POST" }),
  profileUpdateSkool: (profileId: string, payload: { bio?: string; location?: string; socialLinks?: Record<string, string> }) =>
    request<{ success: boolean; updated?: string[] }>(`/profiles/${profileId}/skool-profile`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  profileUploadSkoolPhoto: (profileId: string, file: File) => {
    const form = new FormData();
    form.append("photo", file);
    return request<{ success: boolean; message?: string }>(`/profiles/${profileId}/skool-profile/photo`, {
      method: "POST",
      body: form,
    });
  },
  connectSkool:"""
    new = """  profileResetCounters: (profileId: string) => request<{ success: boolean }>(`/profiles/${profileId}/reset-counters`, { method: "POST" }),
  connectSkool:"""
    if old in c:
        c = c.replace(old, new)
    else:
        # Try without line breaks
        c = re.sub(
            r"  profileUpdateSkool:\([^)]+\)[^}]+}[^}]*}[^,]*,\s*profileUploadSkoolPhoto:[^}]+}[^}]*}[^,]*,\s*",
            "",
            c,
        )

    # Remove skool-profile timeout
    c = c.replace("  if (p.includes(\"/skool-profile\")) return 30000;\n  ", "")
    c = c.replace("\n  if (p.includes(\"/skool-profile\")) return 30000;", "")

    with open(API, "w") as f:
        f.write(c)
    print("api.ts reverted")


def main():
    revert_backend()
    revert_frontend()
    revert_api()
    print("Revert complete")


if __name__ == "__main__":
    main()
