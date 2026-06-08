import { describe, expect, it } from "vitest";

import { getIntelligence } from "./index";
import { LocalIntelligence } from "./local";

describe("LocalIntelligence (offline default)", () => {
  const svc = new LocalIntelligence();

  it("reports itself unavailable (no backend)", async () => {
    expect(await svc.isAvailable()).toBe(false);
  });

  it("returns neutral results without throwing", async () => {
    expect(await svc.fetchInbox()).toEqual([]);
    expect(await svc.forgetting()).toEqual([]);
    expect(await svc.relationshipHealth()).toEqual([]);
    expect(await svc.search("anything")).toEqual([]);
    expect(await svc.graphNeighborhood("n1")).toEqual({ nodes: [], edges: [] });
  });

  it("accepts pushes optimistically while offline", async () => {
    const res = await svc.push([{ title: "t", text: "x", captured_at: "2026-06-08T00:00:00Z" }]);
    expect(res.accepted).toBe(1);
  });

  it("factory returns the offline implementation by default", () => {
    expect(getIntelligence()).toBeInstanceOf(LocalIntelligence);
  });
});
