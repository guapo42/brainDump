/**
 * The IntelligenceService port — the single seam between The External Lobe
 * (client) and the optional Brain Dump backend (specs/04 §3).
 *
 * The client depends ONLY on this interface. `LocalIntelligence` is the default,
 * fully-offline implementation; `BrainDumpIntelligence` (added at P4) is a
 * drop-in adapter over the FastAPI JSON API. Enrichment is merged into local
 * tasks, never replaces them; client-owned fields win on conflict (specs/04 §7).
 *
 * These types are hand-written for P0. Once the backend exposes OpenAPI, the
 * response shapes will be generated and checked against recorded /fixtures so the
 * two sides cannot silently diverge.
 */

export interface SourceRef {
  platform: string; // e.g. "jira", "external_lobe"
  source_id: string; // e.g. "PHX-42"
}

export interface CandidateTask {
  title: string;
  source_ref?: SourceRef;
  project?: string;
  due_date?: string;
  priority?: "low" | "medium" | "high" | "critical";
  estimated_minutes?: number;
}

export interface Enrichment {
  source_ref: SourceRef;
  frustration?: number;
  requesters?: string[];
  context_reasons?: string[];
  days_overdue?: number;
}

export interface ForgettingItem {
  title: string;
  source_ref?: SourceRef;
  frustration: number;
  requesters?: string[];
  context_reasons?: string[];
}

export interface RelationshipHealth {
  person: string;
  health_pct: number;
  trend: "declining" | "stable" | "improving";
  overdue_count: number;
}

export interface GraphNode {
  id: string;
  label: string;
  kind: "person" | "project" | "task" | "source";
}

export interface GraphEdge {
  from: string;
  to: string;
  rel: string;
}

export interface GraphSlice {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface SearchHit {
  source_id: string;
  text: string;
  score: number;
}

export interface PushItem {
  title: string;
  text: string;
  captured_at: string;
}

export interface PushResult {
  accepted: number;
  refs: SourceRef[];
}

export interface IntelligenceService {
  /** External/structured tasks as belt candidates. */
  fetchInbox(opts?: { since?: string }): Promise<CandidateTask[]>;
  /** Enrich tasks with backend intelligence (frustration, requesters, …). */
  enrich(refs: SourceRef[]): Promise<Enrichment[]>;
  /** Frustration-ranked neglected tasks — the object-permanence feed. */
  forgetting(): Promise<ForgettingItem[]>;
  /** Per-stakeholder health for the relationships view. */
  relationshipHealth(): Promise<RelationshipHealth[]>;
  /** A graph neighborhood for the Second Brain force graph. */
  graphNeighborhood(nodeId: string, depth?: number): Promise<GraphSlice>;
  /** Semantic search over the corpus (RAG). */
  search(query: string, n?: number): Promise<SearchHit[]>;
  /** Push locally-captured items up for durable storage + enrichment. */
  push(items: PushItem[]): Promise<PushResult>;
  /** Connectivity probe; UI degrades gracefully when false. */
  isAvailable(): Promise<boolean>;
}
