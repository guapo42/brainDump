# ADR 0004 — Two ICNU models, kept apart

**Status:** accepted · **Date:** 2026-06-08

## Context
"ICNU" exists in two places with different scales and purposes: the product's
0–10 energy-weighted FocusScore (client) and the backend simulation's 0–1
keyword-derived score. Conflating them caused confusion risk.

## Decision
- The **product runtime model is the client's 0–10 energy-weighted FocusScore**
  (External Lobe spec §4.1). It is canonical for all task surfacing.
- The **backend's 0–1 ICNU is validation-only** for backend scoring logic in the
  simulation harness; it is **never shipped to the client**.
- The backend contributes *hints* (priority/tone/keywords → ICNU defaults) and
  the **frustration→urgency bridge** (specs/04 §5), which the Pilot can override.

## Consequences
- No code path mixes the two scales. The bridge mapping lives at the seam.
- The headline acceptance test (high-frustration task surfaces at low energy)
  exercises the bridge, not the backend ICNU.
