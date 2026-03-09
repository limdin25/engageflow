import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

interface ProfileSummary {
  email: string;
  actionsToday: number;
  dailyCap: number;
  status: string;
  lastActionAt: string | null;
  failuresToday: number;
}

interface CommunitySummary {
  name: string;
  profile: string;
  actionsToday: number;
  dailyCap: number;
  editorFailures: number;
  skippedToday: boolean;
  lastFailureReason: string | null;
}

interface QueueSummary {
  pending: number;
  retrying: number;
  skipped: number;
  failedToday: number;
}

interface SkippedPost {
  url: string;
  profile: string;
  reason: string;
  skippedAt: string;
}

interface AdminSummary {
  profiles: ProfileSummary[];
  communities: CommunitySummary[];
  queue: QueueSummary;
  skippedPosts: SkippedPost[];
}

const normalizeBase = (value: string) => value.replace(/\/+$/, "");
const ENV_BASE_URL = (import.meta.env.VITE_BACKEND_URL as string | undefined)?.trim();
const BASE = ENV_BASE_URL ? normalizeBase(ENV_BASE_URL) : "http://localhost:8000";

async function adminFetch(path: string, options?: RequestInit) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  return res.json();
}

function statusColor(actionsToday: number, dailyCap: number, failures: number): string {
  if (failures > 0) return "bg-red-500/10 text-red-400 border-red-500/20";
  if (actionsToday >= dailyCap) return "bg-amber-500/10 text-amber-400 border-amber-500/20";
  return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
}

export default function AdminPage() {
  const [data, setData] = useState<AdminSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      setLoading(true);
      const result = await adminFetch("/admin/summary");
      setData(result);
    } catch {
      toast.error("Failed to load admin summary");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, []);

  const resetCommunityFailures = async (communityId?: string) => {
    await adminFetch("/admin/reset-community-failures", {
      method: "POST",
      body: JSON.stringify(communityId ? { communityId } : {}),
    });
    toast.success(communityId ? "Community failures reset" : "All community failures reset");
    load();
  };

  const unskipPost = async (postUrl: string) => {
    await adminFetch("/admin/unskip-post", {
      method: "POST",
      body: JSON.stringify({ postUrl }),
    });
    toast.success("Post unskipped");
    load();
  };

  const clearSkippedPosts = async () => {
    await adminFetch("/admin/clear-skipped-posts", { method: "POST" });
    toast.success("All skipped posts cleared");
    load();
  };

  const resetDailyCounts = async () => {
    await adminFetch("/admin/reset-daily-counts", { method: "POST" });
    toast.success("Daily counts reset");
    load();
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        Loading admin summary...
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold">Admin Dashboard</h1>

      {/* Card 1: Profiles Today */}
      <div className="rounded-xl border bg-card p-5">
        <h2 className="text-lg font-semibold mb-3">Profiles Today</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="pb-2 pr-4">Email</th>
                <th className="pb-2 pr-4">Actions Today</th>
                <th className="pb-2 pr-4">Daily Cap</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2">Failures Today</th>
              </tr>
            </thead>
            <tbody>
              {data.profiles.map((p) => (
                <tr key={p.email} className="border-b border-border/50">
                  <td className="py-2 pr-4 font-medium">{p.email}</td>
                  <td className="py-2 pr-4">
                    <span className={`inline-block px-2 py-0.5 rounded-md text-xs font-semibold border ${statusColor(p.actionsToday, p.dailyCap, p.failuresToday)}`}>
                      {p.actionsToday} / {p.dailyCap}
                    </span>
                  </td>
                  <td className="py-2 pr-4">{p.dailyCap}</td>
                  <td className="py-2 pr-4 capitalize">{p.status}</td>
                  <td className="py-2">
                    {p.failuresToday > 0 ? (
                      <span className="text-red-400 font-semibold">{p.failuresToday}</span>
                    ) : (
                      <span className="text-muted-foreground">0</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Card 2: Communities */}
      <div className="rounded-xl border bg-card p-5">
        <h2 className="text-lg font-semibold mb-3">Communities</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="pb-2 pr-4">Community</th>
                <th className="pb-2 pr-4">Profile</th>
                <th className="pb-2 pr-4">Actions Today</th>
                <th className="pb-2 pr-4">Cap</th>
                <th className="pb-2 pr-4">Skipped?</th>
                <th className="pb-2 pr-4">Failure Reason</th>
                <th className="pb-2"></th>
              </tr>
            </thead>
            <tbody>
              {data.communities.map((c, i) => (
                <tr key={`${c.name}-${i}`} className="border-b border-border/50">
                  <td className="py-2 pr-4 font-medium">{c.name}</td>
                  <td className="py-2 pr-4 text-muted-foreground">{c.profile}</td>
                  <td className="py-2 pr-4">{c.actionsToday}</td>
                  <td className="py-2 pr-4">{c.dailyCap}</td>
                  <td className="py-2 pr-4">
                    {c.skippedToday ? (
                      <span className="text-red-400 font-semibold">Yes ({c.editorFailures} failures)</span>
                    ) : (
                      <span className="text-muted-foreground">No</span>
                    )}
                  </td>
                  <td className="py-2 pr-4 text-muted-foreground">{c.lastFailureReason || "—"}</td>
                  <td className="py-2">
                    {c.editorFailures > 0 && (
                      <Button size="sm" variant="outline" onClick={() => resetCommunityFailures()}>
                        Reset
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
              {data.communities.length === 0 && (
                <tr><td colSpan={7} className="py-4 text-center text-muted-foreground">No communities</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Card 3: Skipped Posts */}
      <div className="rounded-xl border bg-card p-5">
        <h2 className="text-lg font-semibold mb-3">Skipped Posts</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="pb-2 pr-4">Post URL</th>
                <th className="pb-2 pr-4">Profile</th>
                <th className="pb-2 pr-4">Reason</th>
                <th className="pb-2 pr-4">Skipped At</th>
                <th className="pb-2"></th>
              </tr>
            </thead>
            <tbody>
              {data.skippedPosts.map((sp, i) => (
                <tr key={`${sp.url}-${i}`} className="border-b border-border/50">
                  <td className="py-2 pr-4">
                    <a href={sp.url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline" title={sp.url}>
                      {sp.url.length > 60 ? sp.url.slice(0, 60) + "..." : sp.url}
                    </a>
                  </td>
                  <td className="py-2 pr-4 text-muted-foreground">{sp.profile}</td>
                  <td className="py-2 pr-4 text-muted-foreground">{sp.reason}</td>
                  <td className="py-2 pr-4 text-muted-foreground">{sp.skippedAt}</td>
                  <td className="py-2">
                    <Button size="sm" variant="outline" onClick={() => unskipPost(sp.url)}>
                      Unskip
                    </Button>
                  </td>
                </tr>
              ))}
              {data.skippedPosts.length === 0 && (
                <tr><td colSpan={5} className="py-4 text-center text-muted-foreground">No skipped posts</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Card 4: Quick Actions */}
      <div className="rounded-xl border bg-card p-5">
        <h2 className="text-lg font-semibold mb-3">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <Button variant="outline" onClick={() => resetCommunityFailures()}>
            Reset Community Failures
          </Button>
          <Button variant="outline" onClick={resetDailyCounts}>
            Reset Daily Counts
          </Button>
          <Button variant="outline" onClick={clearSkippedPosts}>
            Clear Skipped Posts
          </Button>
        </div>
        <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
          <div className="rounded-lg border p-3 text-center">
            <div className="text-2xl font-bold">{data.queue.pending}</div>
            <div className="text-muted-foreground">Pending</div>
          </div>
          <div className="rounded-lg border p-3 text-center">
            <div className="text-2xl font-bold">{data.queue.retrying}</div>
            <div className="text-muted-foreground">Retrying</div>
          </div>
          <div className="rounded-lg border p-3 text-center">
            <div className="text-2xl font-bold">{data.queue.skipped}</div>
            <div className="text-muted-foreground">Skipped</div>
          </div>
          <div className="rounded-lg border p-3 text-center">
            <div className="text-2xl font-bold text-red-400">{data.queue.failedToday}</div>
            <div className="text-muted-foreground">Failed Today</div>
          </div>
        </div>
      </div>
    </div>
  );
}
