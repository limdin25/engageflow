/**
 * TDD: Activity Timeline dedupe + interleave helpers.
 */
import { describe, expect, it } from "vitest";
import { dedupeActivities, interleaveByProfile } from "./activityTimeline";
import type { ActivityEntry } from "./types";

const mk = (overrides: Partial<ActivityEntry> & { id: string; profile: string; timestamp: string }): ActivityEntry =>
  ({ groupName: "group", action: "Commented", postUrl: "https://x.com/p1", ...overrides });

describe("dedupeActivities", () => {
  it("dedupe removes exact duplicates by id", () => {
    const a = mk({ id: "1", profile: "alice", timestamp: "2025-01-01T12:00:00Z" });
    const dup = mk({ id: "1", profile: "alice", timestamp: "2025-01-01T12:00:00Z" });
    const b = mk({ id: "2", profile: "bob", timestamp: "2025-01-01T11:00:00Z" });
    const result = dedupeActivities([a, dup, b]);
    expect(result).toHaveLength(2);
    expect(result.map((x) => x.id)).toEqual(["1", "2"]);
  });

  it("dedupe removes duplicates by profile+groupName+action+timestamp when id missing", () => {
    const a = mk({ id: "", profile: "alice", groupName: "g1", action: "Commented", timestamp: "2025-01-01T12:00:00Z" });
    const dup = mk({ id: "", profile: "alice", groupName: "g1", action: "Commented", timestamp: "2025-01-01T12:00:00Z" });
    const result = dedupeActivities([a, dup]);
    expect(result).toHaveLength(1);
  });
});

describe("interleaveByProfile", () => {
  it("interleaves by profile while preserving per-profile order", () => {
    const alice1 = mk({ id: "a1", profile: "alice", timestamp: "2025-01-01T12:00:00Z" });
    const alice2 = mk({ id: "a2", profile: "alice", timestamp: "2025-01-01T11:00:00Z" });
    const bob1 = mk({ id: "b1", profile: "bob", timestamp: "2025-01-01T11:30:00Z" });
    const input = [alice1, alice2, bob1]; // newest-first per backend
    const result = interleaveByProfile(input);
    expect(result).toHaveLength(3);
    // Round-robin: alice, bob, alice (or bob, alice, alice depending on profile order)
    const profiles = result.map((x) => x.profile);
    expect(profiles[0]).not.toBe(profiles[1] ?? profiles[0]); // first two differ when 2+ profiles
    // Within alice: a1 (newer) before a2 (older)
    const aliceIndices = result.map((r, i) => (r.profile === "alice" ? i : -1)).filter((i) => i >= 0);
    expect(result[aliceIndices[0]!].id).toBe("a1");
    expect(result[aliceIndices[1]!].id).toBe("a2");
  });

  it("interleave result length equals input length after dedupe", () => {
    const items = [
      mk({ id: "1", profile: "alice", timestamp: "2025-01-01T12:00:00Z" }),
      mk({ id: "2", profile: "bob", timestamp: "2025-01-01T11:00:00Z" }),
      mk({ id: "3", profile: "alice", timestamp: "2025-01-01T10:00:00Z" }),
    ];
    const deduped = dedupeActivities(items);
    const interleaved = interleaveByProfile(deduped);
    expect(interleaved).toHaveLength(deduped.length);
    expect(interleaved).toHaveLength(3);
  });
});
