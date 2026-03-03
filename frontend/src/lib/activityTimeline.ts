/**
 * Activity Timeline display helpers: dedupe + interleave by profile.
 * Input is assumed newest-first (backend ORDER BY timestamp DESC).
 */
import type { ActivityEntry } from "./types";

/** Stable key for deduplication: prefer id, else profile+groupName+action+timestamp. */
function stableKey(item: ActivityEntry): string {
  if (item.id && String(item.id).trim()) {
    return String(item.id);
  }
  return `${item.profile}|${item.groupName}|${item.action}|${item.timestamp}`;
}

/**
 * Remove exact duplicates by stable key. First occurrence wins (preserves order).
 */
export function dedupeActivities(items: ActivityEntry[]): ActivityEntry[] {
  const seen = new Set<string>();
  const out: ActivityEntry[] = [];
  for (const item of items) {
    const key = stableKey(item);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(item);
  }
  return out;
}

/**
 * Interleave by profile (round-robin), preserving within-profile order (newest→oldest).
 * Input must be newest-first. Output: no two consecutive items from same profile when 2+ profiles.
 */
export function interleaveByProfile(items: ActivityEntry[]): ActivityEntry[] {
  const byProfile = new Map<string, ActivityEntry[]>();
  const profileOrder: string[] = [];
  for (const item of items) {
    const key = String(item.profile || "");
    if (!byProfile.has(key)) {
      byProfile.set(key, []);
      profileOrder.push(key);
    }
    byProfile.get(key)!.push(item);
  }
  const out: ActivityEntry[] = [];
  while (true) {
    let tookAny = false;
    for (const key of profileOrder) {
      const bucket = byProfile.get(key);
      if (!bucket || bucket.length === 0) continue;
      const next = bucket.shift()!;
      out.push(next);
      tookAny = true;
    }
    if (!tookAny) break;
  }
  return out;
}
