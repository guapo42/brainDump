# ADR 0003 — The IntelligenceService port is the only seam

**Status:** accepted · **Date:** 2026-06-08

## Context
The client and the optional backend must integrate without coupling, and the
frontend must be fully buildable/testable before the backend exists.

## Decision
A single **`IntelligenceService`** interface is the only integration boundary
(specs/04 §3). Two implementations: `LocalIntelligence` (default, offline,
heuristic) and `BrainDumpIntelligence` (adapter over the FastAPI JSON API, added
at P4). App code reaches the backend **only** via the `getIntelligence()` factory
— never a concrete adapter, never `fetch` to the backend (ESLint-enforced).

## Consequences
- Frontend is built/tested stub-first against `LocalIntelligence` + recorded
  `/fixtures`.
- Port shape and backend responses are kept in lockstep via shared fixtures (and,
  once the API exists, generated types). The seam contract test is the guard.
- Adding/replacing the backend is a drop-in, not an architecture change.
