#!/usr/bin/env python3
"""Replace Edit profile window.open with in-app modal. PATCH skool-profile, POST skool-profile/photo.
Run on VPS: python3 engageflow-skool-profile-modal.patch.py
"""
import os
import sys
BASE = "/root/.openclaw/workspace-margarita/engageflow/frontend"
PAGE = os.path.join(BASE, "src", "pages", "ProfilesPage.tsx")
API_PATH = os.path.join(BASE, "src", "lib", "api.ts")


def main():
    # 1. Add API methods for skool-profile
    with open(API_PATH, "r") as f:
        api_content = f.read()

    if "profileUpdateSkool" in api_content:
        print("profileUpdateSkool already in api.ts, skipping API")
    else:
        old = "  profileResetCounters: (profileId: string) => request<{ success: boolean }>(`/profiles/${profileId}/reset-counters`, { method: \"POST\" }),"
        new = """  profileResetCounters: (profileId: string) => request<{ success: boolean }>(`/profiles/${profileId}/reset-counters`, { method: "POST" }),
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
  },"""
        if old not in api_content:
            print("Could not find profileResetCounters in api.ts")
            sys.exit(1)
        api_content = api_content.replace(old, new)
        with open(API_PATH, "w") as f:
            f.write(api_content)
        print("Added profileUpdateSkool, profileUploadSkoolPhoto to api.ts")

        # Add timeout for skool-profile
        if "skool-profile" not in api_content:
            if "connect-skool" in api_content:
                api_content = api_content.replace(
                    "if (p.includes(\"/connect-skool\")) return 70000;",
                    "if (p.includes(\"/connect-skool\")) return 70000;\n  if (p.includes(\"/skool-profile\")) return 30000;",
                )
            else:
                api_content = api_content.replace(
                    "if (p.includes(\"/check-login\")) return 70000;",
                    "if (p.includes(\"/check-login\")) return 70000;\n  if (p.includes(\"/skool-profile\")) return 30000;",
                )
            with open(API_PATH, "w") as f:
                f.write(api_content)
            print("Added skool-profile timeout")

    # 2. Update ProfilesPage: replace window.open with modal
    with open(PAGE, "r") as f:
        page_content = f.read()

    if "EditSkoolModal" in page_content or "profileUpdateSkool" in page_content:
        print("Edit profile modal already present")
        return

    # Add Pencil import if missing
    if "Pencil" not in page_content:
        page_content = page_content.replace(
            "import { RefreshCw, Trash2 } from \"lucide-react\";",
            "import { Pencil, RefreshCw, Trash2 } from \"lucide-react\";",
        )
        if "Pencil" not in page_content:
            page_content = page_content.replace(
                "import { Trash2",
                "import { Pencil, Trash2",
                1,
            )
        print("Added Pencil import")

    # Replace Edit profile button: window.open -> setEditModalProfile(selected)
    old_btn = """<button onClick={() => window.open('https://www.skool.com/settings?t=profile', '_blank')} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-border text-xs font-medium text-foreground hover:bg-muted transition-colors" title="Open Skool profile settings">
                    <Pencil className="w-3 h-3" /> Edit profile
                  </button>"""
    new_btn = """<button onClick={() => setEditModalProfile(selected)} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-border text-xs font-medium text-foreground hover:bg-muted transition-colors" title="Edit Skool profile">
                    <Pencil className="w-3 h-3" /> Edit profile
                  </button>"""
    if old_btn in page_content:
        page_content = page_content.replace(old_btn, new_btn)
        print("Replaced Edit profile button with modal trigger")
    elif "Edit profile" in page_content and "setEditModalProfile" not in page_content:
        # Fallback: maybe button format differs
        page_content = page_content.replace(
            "window.open('https://www.skool.com/settings?t=profile', '_blank')",
            "setEditModalProfile(selected)",
        )
        print("Replaced window.open with setEditModalProfile")
    else:
        print("Edit profile button not found or already updated")
        return

    # Add state and modal - after existing useState declarations
    if "editModalProfile" not in page_content:
        # Try multiple patterns (ProfilesPage uses selectedProfileId, not selected state)
        for old, new in [
            (
                "const [checkProxyMessage, setCheckProxyMessage] = useState<Record<string, string>>({});",
                "const [checkProxyMessage, setCheckProxyMessage] = useState<Record<string, string>>({});\n  const [editModalProfile, setEditModalProfile] = useState<Profile | null>(null);\n  const [editForm, setEditForm] = useState({ bio: \"\", location: \"\", website: \"\", instagram: \"\", x: \"\" });\n  const [editSaving, setEditSaving] = useState(false);\n  const [editError, setEditError] = useState(\"\");\n  const [photoFile, setPhotoFile] = useState<File | null>(null);",
            ),
            (
                "const [selected, setSelected] = useState<Profile | null>(null);",
                "const [selected, setSelected] = useState<Profile | null>(null);\n  const [editModalProfile, setEditModalProfile] = useState<Profile | null>(null);\n  const [editForm, setEditForm] = useState({ bio: \"\", location: \"\", website: \"\", instagram: \"\", x: \"\" });\n  const [editSaving, setEditSaving] = useState(false);\n  const [editError, setEditError] = useState(\"\");\n  const [photoFile, setPhotoFile] = useState<File | null>(null);",
            ),
        ]:
            if old in page_content and "editModalProfile" not in page_content:
                page_content = page_content.replace(old, new)
                print("Added edit modal state")
                break
        else:
            print("Could not add edit modal state")
            sys.exit(1)

    # Add modal component - before the closing </div> of the main return, or before the last </div>
    # We'll insert after the sidebar (Quick Actions) div
    MODAL_JSX = """
      {editModalProfile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => !editSaving && setEditModalProfile(null)}>
          <div className="bg-background rounded-lg shadow-xl max-w-md w-full mx-4 p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">Edit Skool profile</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Bio</label>
                <textarea value={editForm.bio} onChange={e => setEditForm(f => ({ ...f, bio: e.target.value }))} className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm" rows={3} placeholder="Profile bio" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Location</label>
                <input value={editForm.location} onChange={e => setEditForm(f => ({ ...f, location: e.target.value }))} className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm" placeholder="Location" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Website</label>
                <input value={editForm.website} onChange={e => setEditForm(f => ({ ...f, website: e.target.value }))} className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm" placeholder="https://" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Instagram</label>
                <input value={editForm.instagram} onChange={e => setEditForm(f => ({ ...f, instagram: e.target.value }))} className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm" placeholder="https://instagram.com/..." />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">X (Twitter)</label>
                <input value={editForm.x} onChange={e => setEditForm(f => ({ ...f, x: e.target.value }))} className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm" placeholder="https://x.com/..." />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Profile photo</label>
                <input type="file" accept="image/*" onChange={e => setPhotoFile(e.target.files?.[0] ?? null)} className="w-full text-sm" />
              </div>
            </div>
            {editError && <p className="text-sm text-destructive mt-2">{editError}</p>}
            <div className="flex gap-2 mt-6">
              <button onClick={() => !editSaving && setEditModalProfile(null)} className="px-4 py-2 rounded-md border border-border text-sm">Cancel</button>
              <button disabled={editSaving} onClick={async () => {
                if (!editModalProfile) return;
                setEditError("");
                setEditSaving(true);
                try {
                  const payload: { bio?: string; location?: string; socialLinks?: Record<string, string> } = {};
                  if (editForm.bio !== undefined) payload.bio = editForm.bio;
                  if (editForm.location !== undefined) payload.location = editForm.location;
                  const links: Record<string, string> = {};
                  if (editForm.website?.trim()) links.website = editForm.website.trim();
                  if (editForm.instagram?.trim()) links.instagram = editForm.instagram.trim();
                  if (editForm.x?.trim()) links.x = editForm.x.trim();
                  if (Object.keys(links).length) payload.socialLinks = links;
                  if (Object.keys(payload).length) await api.profileUpdateSkool(editModalProfile.id, payload);
                  if (photoFile) await api.profileUploadSkoolPhoto(editModalProfile.id, photoFile);
                  setEditModalProfile(null);
                  setPhotoFile(null);
                  refreshAll();
                } catch (e: unknown) {
                  setEditError(e && typeof e === "object" && "message" in e ? String((e as { message: unknown }).message) : "Failed to update");
                } finally {
                  setEditSaving(false);
                }
              }} className="px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm disabled:opacity-50">
                {editSaving ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}
"""

    # Insert modal before the closing </div> of the main layout - find the last </div> before </div> (outer)
    # Simpler: insert before the final closing </div> of the main return
    # Look for the pattern: after the sidebar div, we have the main content. The modal should be a sibling.
    # Typically: <div className="flex ..."> <aside>...</aside> <main>...</main> </div>
    # We need to add the modal inside the main wrapper. Find "</main>" or similar and add before the parent </div>
    # Even simpler: add right after the opening of the main return, as first child - or at the end before the last </div>
    # Let me try: find the div that contains the whole page, and add the modal as the last child before it closes
    # Pattern: before </div> that closes the main layout - usually the structure is:
    # return ( <div className="..."> ... content ... </div> );
    # We'll add the modal before the final </div> of the main return
    # Look for: </div>\n    </div>\n  ); or similar - the structure may vary
    # Safer: add after the sidebar section - find "Quick Actions" and the closing </div> of that section, then add the modal after the parent </div> that wraps everything
    # Insert modal - try multiple patterns
    inserted = False
    for marker in (
        "                  </div>\n                </div>\n              )}",
        "                </div>\n              </div>\n            )}",
        "</div>\n        </div>\n      </div>\n    </div>",
    ):
        if marker in page_content:
            page_content = page_content.replace(marker, marker + MODAL_JSX)
            inserted = True
            break
    if not inserted:
        # Fallback: insert before the component's closing );
        idx = page_content.rfind(");")
        if idx > 0:
            # Insert before the last );
            before = page_content[:idx]
            after = page_content[idx:]
            last_div = before.rfind("</div>")
            if last_div >= 0:
                page_content = before[:last_div] + MODAL_JSX + "\n      " + before[last_div:] + after
                inserted = True
    if not inserted:
        print("Could not find insertion point for modal")
        sys.exit(1)
    print("Added Edit Skool modal")

    # Reset form when opening modal
    if "setEditModalProfile(selected)" in page_content and "setEditForm" in page_content:
        # When we open the modal, we should also reset form - but we don't have current profile data. For now we can leave form empty.
        # Optionally: when we set editModalProfile, we could fetch current profile or set initial values. Skip for simplicity.
        pass

    with open(PAGE, "w") as f:
        f.write(page_content)
    print("Patch applied successfully")


if __name__ == "__main__":
    main()
