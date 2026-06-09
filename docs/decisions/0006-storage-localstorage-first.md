# ADR 0006 — localStorage first, IndexedDB behind the same seam

**Status:** accepted · **Date:** 2026-06-09

## Context
The External Lobe spec names IndexedDB/localStorage for persistence; the P0
scaffold's `safeStorage` wraps **localStorage**; Zustand `persist` defaults to
localStorage. These need reconciling before stores land (P2). localStorage is
synchronous and simple but quota-limited (~5 MB); IndexedDB is async and roomy
but more machinery. Projected v1 data (tasks, captures, FSM state, undo window,
a cached graph slice) fits comfortably under the localStorage quota.

## Decision
**v1 persists to localStorage, exclusively through `safeStorage`.** Zustand
`persist` uses a `safeStorage`-backed storage adapter. The adapter interface is
the seam: swapping to IndexedDB (e.g. `idb-keyval`) later is a storage-adapter
change, not a store or component change.

**Trigger to revisit:** quota warn-once events observed in real use, or any
single persisted store exceeding ~2 MB (watch the undo history and cached graph
slices — cap them rather than grow them).

## Consequences
- CLAUDE.md's "IndexedDB/localStorage via safeStorage" reads as: localStorage
  today, IndexedDB later, same wrapper either way.
- Nothing outside the storage adapter may know which backend is in use.
- Caps stay enforced in code (undo ≤ 200 entries / 1 h; history ≤ 50; graph
  slice cache = last slice only).
