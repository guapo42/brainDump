/**
 * The only sanctioned gateway to Web Storage. Every persisted read/write goes
 * through here (CLAUDE.md Part VII). Guards against SSR (no window), disabled or
 * blocked storage, quota overflow, and corrupt JSON — warning once per failure
 * mode rather than throwing into the UI.
 */

type FailureMode = "unavailable" | "read" | "write" | "quota" | "parse";

const warned = new Set<FailureMode>();

function warnOnce(mode: FailureMode, detail: unknown): void {
  if (warned.has(mode)) return;
  warned.add(mode);
  console.warn(`[safeStorage] ${mode}:`, detail);
}

function backend(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage;
  } catch (err) {
    warnOnce("unavailable", err);
    return null;
  }
}

/** Read and parse a JSON value; returns `fallback` on any failure. */
export function getJSON<T>(key: string, fallback: T): T {
  const store = backend();
  if (!store) return fallback;

  let raw: string | null;
  try {
    raw = store.getItem(key);
  } catch (err) {
    warnOnce("read", err);
    return fallback;
  }
  if (raw === null) return fallback;

  try {
    return JSON.parse(raw) as T;
  } catch (err) {
    warnOnce("parse", err);
    // Corrupt payload: drop it so it can't poison future reads.
    try {
      store.removeItem(key);
    } catch {
      /* best-effort */
    }
    return fallback;
  }
}

/** Serialize and persist a JSON value; returns whether it was stored. */
export function setJSON(key: string, value: unknown): boolean {
  const store = backend();
  if (!store) return false;
  try {
    store.setItem(key, JSON.stringify(value));
    return true;
  } catch (err) {
    const quota =
      err instanceof DOMException &&
      (err.name === "QuotaExceededError" || err.name === "NS_ERROR_DOM_QUOTA_REACHED");
    warnOnce(quota ? "quota" : "write", err);
    return false;
  }
}

/** Remove a key; best-effort. */
export function remove(key: string): void {
  const store = backend();
  if (!store) return;
  try {
    store.removeItem(key);
  } catch (err) {
    warnOnce("write", err);
  }
}

/** Test-only: clear the once-per-mode warning latch. */
export function __resetWarnings(): void {
  warned.clear();
}
