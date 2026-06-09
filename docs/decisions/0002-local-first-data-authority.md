# ADR 0002 — Local-first data authority; backend syncs

**Status:** accepted · **Date:** 2026-06-08

## Context
Where does task/state truth live — the client or the Neo4j-backed backend? This
drives data flow, offline behavior, and sync throughout.

## Decision
**The client is authoritative for live cognitive state** (energy, focus FSM,
captures, tasks-on-the-belt), persisted to IndexedDB via `safeStorage`. The Brain
Dump backend ingests external sources (Jira/email) and pushes **enrichment**
(frustration/forgetting, requesters, graph slices) that is **merged additively**
into local tasks. Client-owned fields win on conflict (specs/04 §7).

## Consequences
- The app is fully usable offline (principle P2/P5); the backend never blocks the
  UI and is never required for core function.
- Sync is async, additive, queue-on-offline. No multi-device/auth in v1 (single
  local user).
- The backend must stay **stateless about live cognitive state** (CLAUDE.md III).
