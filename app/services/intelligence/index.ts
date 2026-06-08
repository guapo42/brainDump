/**
 * The seam factory. App code (components/stores/hooks) imports `getIntelligence`
 * and the port types from here — never a concrete adapter, never the backend
 * directly (enforced by the ESLint boundary rule).
 *
 * P0 always returns the offline `LocalIntelligence`. P4 adds selection of
 * `BrainDumpIntelligence` when the backend is reachable.
 */

import { LocalIntelligence } from "./local";
import type { IntelligenceService } from "./types";

let instance: IntelligenceService | null = null;

export function getIntelligence(): IntelligenceService {
  if (!instance) instance = new LocalIntelligence();
  return instance;
}

/** Test-only: override the active implementation. */
export function __setIntelligence(svc: IntelligenceService | null): void {
  instance = svc;
}

export type { IntelligenceService } from "./types";
