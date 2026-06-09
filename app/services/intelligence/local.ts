/**
 * LocalIntelligence — the default, fully-offline implementation of the
 * IntelligenceService seam. The app is always usable on this alone (specs/04 §3).
 *
 * P0 is a working skeleton: every method returns an empty/neutral result and
 * `isAvailable()` is false. Later phases grow real local heuristics (a
 * client-side frustration estimate, a local task graph, keyword search) — but
 * the contract and the offline guarantee start here.
 */

import type {
  CandidateTask,
  Enrichment,
  ForgettingItem,
  GraphSlice,
  IntelligenceService,
  PushItem,
  PushResult,
  RelationshipHealth,
  SearchHit,
  SourceRef,
} from "./types";

export class LocalIntelligence implements IntelligenceService {
  async fetchInbox(): Promise<CandidateTask[]> {
    return [];
  }

  async enrich(_refs: SourceRef[]): Promise<Enrichment[]> {
    return [];
  }

  async forgetting(): Promise<ForgettingItem[]> {
    return [];
  }

  async relationshipHealth(): Promise<RelationshipHealth[]> {
    return [];
  }

  async graphNeighborhood(_nodeId: string, _depth = 1): Promise<GraphSlice> {
    return { nodes: [], edges: [] };
  }

  async search(_query: string, _n = 5): Promise<SearchHit[]> {
    return [];
  }

  async push(items: PushItem[]): Promise<PushResult> {
    // Offline: nothing durable happens, but accept everything so callers don't block.
    return { accepted: items.length, refs: [] };
  }

  async isAvailable(): Promise<boolean> {
    return false;
  }
}
