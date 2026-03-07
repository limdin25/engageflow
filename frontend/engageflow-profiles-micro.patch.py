#!/usr/bin/env python3
"""Patch EngageFlow: add Micro badge and Added timestamp to ProfilesPage.
Run on VPS: python3 engageflow-profiles-micro.patch.py
"""
import os
BASE = "/root/.openclaw/workspace-margarita/engageflow/frontend"

def main():
    # 1. Add source and connected_at to Profile in types.ts
    types_path = os.path.join(BASE, "src", "lib", "types.ts")
    with open(types_path, "r") as f:
        types_content = f.read()

    if "source?: string" in types_content and "connected_at?: string" in types_content:
        print("Profile already has source/connected_at in types.ts, skipping")
    else:
        old = """  status: "running" | "paused" | "idle" | "checking" | "ready" | "blocked" | "captcha" | "logged_out" | string;
  dailyUsage: number;
  groupsConnected: number;
}

export interface Community"""
        new = """  status: "running" | "paused" | "idle" | "checking" | "ready" | "blocked" | "captcha" | "logged_out" | string;
  dailyUsage: number;
  groupsConnected: number;
  source?: string;
  connected_at?: string;
}

export interface Community"""
        if old in types_content:
            types_content = types_content.replace(old, new)
            with open(types_path, "w") as f:
                f.write(types_content)
            print("Added source, connected_at to Profile type")
        else:
            print("Profile type block not found")

    # 2. Add Micro badge and Added timestamp to ProfilesPage
    page_path = os.path.join(BASE, "src", "pages", "ProfilesPage.tsx")
    with open(page_path, "r") as f:
        page_content = f.read()

    if "Micro" in page_content and "profile.source" in page_content:
        print("ProfilesPage already has Micro badge, skipping")
    else:
        # Add Micro badge next to profile name
        old_name = """<p className="text-sm font-semibold text-foreground truncate">{profile.name}</p>
                    <div className="flex items-center gap-1.5 mt-0.5">"""
        new_name = """<div className="flex items-center gap-1.5 flex-wrap">
                      <p className="text-sm font-semibold text-foreground truncate">{profile.name}</p>
                      {profile.source === "micro" && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-primary/20 text-primary">Micro</span>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 mt-0.5">"""
        if old_name in page_content:
            page_content = page_content.replace(old_name, new_name)
            print("Added Micro badge")
        else:
            print("Profile name block not found for Micro badge")

        # Add Added timestamp - after "X groups" line
        old_groups = """<div className="flex justify-between text-xs text-muted-foreground mb-2">
                  <span>{profile.groupsConnected} groups</span>
                </div>"""
        new_groups = """<div className="flex justify-between text-xs text-muted-foreground mb-2">
                  <span>{profile.groupsConnected} groups</span>
                  {profile.connected_at && (
                    <span>Added {new Date(profile.connected_at).toLocaleDateString()}</span>
                  )}
                </div>"""
        if old_groups in page_content and "profile.connected_at" not in page_content:
            page_content = page_content.replace(old_groups, new_groups)
            print("Added Added timestamp")
        elif "profile.connected_at" in page_content:
            print("Added timestamp already present")
        else:
            print("Groups block not found for Added timestamp")

        with open(page_path, "w") as f:
            f.write(page_content)

    print("Profiles patch applied successfully")


if __name__ == "__main__":
    main()
