// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";

import { __resetWarnings, getJSON, remove, setJSON } from "./safe-storage";

afterEach(() => {
  localStorage.clear();
  __resetWarnings();
  vi.restoreAllMocks();
});

describe("safeStorage", () => {
  it("round-trips JSON values", () => {
    expect(setJSON("k", { a: 1 })).toBe(true);
    expect(getJSON("k", null)).toEqual({ a: 1 });
  });

  it("returns the fallback for a missing key", () => {
    expect(getJSON("absent", "fallback")).toBe("fallback");
  });

  it("drops corrupt JSON and returns the fallback", () => {
    localStorage.setItem("bad", "{not json");
    expect(getJSON("bad", 42)).toBe(42);
    // corrupt payload removed so it can't poison future reads
    expect(localStorage.getItem("bad")).toBeNull();
  });

  it("warns once and survives a QuotaExceededError on write", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("full", "QuotaExceededError");
    });
    expect(setJSON("k", "v")).toBe(false);
    expect(setJSON("k2", "v2")).toBe(false);
    expect(warn).toHaveBeenCalledTimes(1); // once per failure mode
  });

  it("removes keys", () => {
    setJSON("k", 1);
    remove("k");
    expect(getJSON("k", null)).toBeNull();
  });
});
