/**
 * TDD: resolveBackendBaseUrl determinism — DEV uses only VITE_BACKEND_URL when set.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

describe("resolveBackendBaseUrl / getBackendBaseUrl", () => {
  const savedLocation = window.location;

  beforeEach(() => {
    vi.resetModules();
  });

  afterEach(() => {
    Object.defineProperty(window, "location", {
      value: savedLocation,
      writable: true,
    });
  });

  it("uses VITE_BACKEND_URL when set (no fallback probing)", async () => {
    // Simulate build with VITE_BACKEND_URL set — module must use it exclusively.
    vi.stubEnv("VITE_BACKEND_URL", "https://engageflow-dev.up.railway.app");
    const { getBackendBaseUrl: getBase } = await import("./api");
    const base = await getBase();
    expect(base).toBe("https://engageflow-dev.up.railway.app");
    vi.unstubAllEnvs();
  });

  it("throws when deployed (non-localhost) and VITE_BACKEND_URL not set", async () => {
    Object.defineProperty(window, "location", {
      value: {
        hostname: "selfless-renewal-dev.up.railway.app",
        origin: "https://selfless-renewal-dev.up.railway.app",
        protocol: "https:",
      },
      writable: true,
    });
    vi.stubEnv("VITE_BACKEND_URL", "");
    const { getBackendBaseUrl: getBase } = await import("./api");
    await expect(getBase()).rejects.toThrow("VITE_BACKEND_URL must be set when deployed");
    vi.unstubAllEnvs();
  });
});
