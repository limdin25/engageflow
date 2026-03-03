#!/usr/bin/env python3
"""Patch EngageFlow frontend: add ConnectPage and /connect route.
Run on VPS: python3 engageflow-connect-frontend.patch.py
"""
import os
BASE = "/root/.openclaw/workspace-margarita/engageflow/frontend"

CONNECT_PAGE = '''import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { CheckCircle2, Loader2, Zap } from "lucide-react";

export default function ConnectPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [connected, setConnected] = useState(false);
  const [profileId, setProfileId] = useState<string | null>(null);

  const handleConnect = async () => {
    setError("");
    if (!email.trim() || !password.trim()) {
      setError("Email and password are required");
      return;
    }
    setLoading(true);
    try {
      const res = await api.connectSkool({ email: email.trim(), password });
      if (res?.success && res?.profileId) {
        setProfileId(res.profileId);
        setConnected(true);
      } else {
        setError(res?.message || "Connection failed");
      }
    } catch (e: unknown) {
      const msg = e && typeof e === "object" && "message" in e ? String((e as { message: unknown }).message) : "Connection failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = () => {
    setConnected(false);
    setProfileId(null);
    setError("");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-white">
      <div className="w-full max-w-sm mx-auto px-6">
        <div className="flex flex-col items-center mb-8">
          <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-primary mb-4">
            <Zap className="w-6 h-6 text-primary-foreground" />
          </div>
          <h1 className="text-xl font-semibold text-foreground">Connect Skool</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {connected ? "Your account is connected" : "Enter your Skool credentials"}
          </p>
        </div>

        {connected ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2 p-4 rounded-lg bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800">
              <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0" />
              <span className="text-sm font-medium text-green-700 dark:text-green-400">Connected</span>
            </div>
            <Button variant="outline" onClick={handleDisconnect} className="w-full">
              Disconnect
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            <Input
              type="email"
              placeholder="Skool email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setError(""); }}
              onKeyDown={(e) => e.key === "Enter" && handleConnect()}
            />
            <Input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setError(""); }}
              onKeyDown={(e) => e.key === "Enter" && handleConnect()}
            />
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button onClick={handleConnect} disabled={loading} className="w-full">
              {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Connect
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
'''

def main():
    # 1. Create ConnectPage.tsx
    page_path = os.path.join(BASE, "src", "pages", "ConnectPage.tsx")
    with open(page_path, "w") as f:
        f.write(CONNECT_PAGE)
    print(f"Created {page_path}")

    # 2. Add connectSkool to api.ts
    api_path = os.path.join(BASE, "src", "lib", "api.ts")
    with open(api_path, "r") as f:
        api_content = f.read()

    if "connectSkool" in api_content:
        print("connectSkool already in api.ts, skipping")
    else:
        # Add after profileCheckLogin or profileResetCounters
        old = "  profileResetCounters: (profileId: string) => request<{ success: boolean }>(`/profiles/${profileId}/reset-counters`, { method: \"POST\" }),"
        new = """  profileResetCounters: (profileId: string) => request<{ success: boolean }>(`/profiles/${profileId}/reset-counters`, { method: "POST" }),
  connectSkool: (payload: { email: string; password: string }) =>
    request<{ success: boolean; profileId?: string; message?: string }>("/connect-skool", {
      method: "POST",
      body: JSON.stringify(payload),
    }),"""
        if old not in api_content:
            print("Could not find insertion point in api.ts")
            return
        api_content = api_content.replace(old, new)
        with open(api_path, "w") as f:
            f.write(api_content)
        print("Added connectSkool to api.ts")

    # 3. Add timeout for connect-skool in api.ts
    if 'p.includes("/connect-skool")' not in api_content:
        old_timeout = "  if (p.includes(\"/check-login\")) return 70000;"
        new_timeout = "  if (p.includes(\"/check-login\")) return 70000;\n  if (p.includes(\"/connect-skool\")) return 70000;"
        api_content = api_content.replace(old_timeout, new_timeout)
        with open(api_path, "w") as f:
            f.write(api_content)
        print("Added connect-skool timeout")

    # 4. Add /connect route to App.tsx
    app_path = os.path.join(BASE, "src", "App.tsx")
    with open(app_path, "r") as f:
        app_content = f.read()

    if "ConnectPage" in app_content:
        print("ConnectPage route already in App.tsx, skipping")
    else:
        # Add import
        app_content = app_content.replace(
            "import OwnerPage from \"./pages/OwnerPage\";",
            "import OwnerPage from \"./pages/OwnerPage\";\nimport ConnectPage from \"./pages/ConnectPage\";",
        )
        # Add route - /connect should be public like /lock
        app_content = app_content.replace(
            "<Route path=\"/owner\" element={<OwnerPage />} />",
            "<Route path=\"/owner\" element={<OwnerPage />} />\n            <Route path=\"/connect\" element={<ConnectPage />} />",
        )
        with open(app_path, "w") as f:
            f.write(app_content)
        print("Added /connect route to App.tsx")

    print("Frontend patch applied successfully")


if __name__ == "__main__":
    main()
