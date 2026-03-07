#!/usr/bin/env python3
"""Add Edit profile button to EngageFlow ProfilesPage. Opens Skool profile settings in new tab.
Run on VPS: python3 engageflow-edit-profile.patch.py
"""
import os
PAGE = "/root/.openclaw/workspace-margarita/engageflow/frontend/src/pages/ProfilesPage.tsx"

def main():
    with open(PAGE, "r") as f:
        content = f.read()

    if "Edit profile" in content and "skool.com/settings" in content:
        print("Edit profile button already present")
        return

    # Add Edit profile button before Delete
    old = """                  <button className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-border text-xs font-medium text-foreground hover:bg-muted transition-colors">
                    <RefreshCw className="w-3 h-3" /> Force Re-scan
                  </button>
                  <button onClick={() => deleteProfile(selected.id)} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-destructive text-xs font-medium text-destructive hover:bg-destructive/10 transition-colors">
                    <Trash2 className="w-3 h-3" /> Delete
                  </button>"""
    new = """                  <button className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-border text-xs font-medium text-foreground hover:bg-muted transition-colors">
                    <RefreshCw className="w-3 h-3" /> Force Re-scan
                  </button>
                  <button onClick={() => window.open('https://www.skool.com/settings?t=profile', '_blank')} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-border text-xs font-medium text-foreground hover:bg-muted transition-colors" title="Open Skool profile settings">
                    <Pencil className="w-3 h-3" /> Edit profile
                  </button>
                  <button onClick={() => deleteProfile(selected.id)} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-destructive text-xs font-medium text-destructive hover:bg-destructive/10 transition-colors">
                    <Trash2 className="w-3 h-3" /> Delete
                  </button>"""
    if old in content:
        content = content.replace(old, new)
        with open(PAGE, "w") as f:
            f.write(content)
        print("Added Edit profile button")
    else:
        print("Target block not found")
        return

    print("Patch applied successfully")


if __name__ == "__main__":
    main()
