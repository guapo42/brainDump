# ADR 0001 — React/Next local-first frontend (supersedes htmx)

**Status:** accepted · **Date:** 2026-06-08

## Context
An early decision picked htmx + server-rendered FastAPI for the UI. The product
vision (*The External Lobe*) is a rich client: client-side FSM, rAF force-directed
graph, 60bpm SVG animation, <100ms offline interactions, voice capture. htmx
cannot deliver these without round-tripping the server.

## Decision
The frontend is **React/Next (App Router) + TypeScript**, local-first. Brain Dump
becomes an optional Python intelligence service behind the `IntelligenceService`
seam (ADR 0003). FastAPI is a **JSON API only** — no server-rendered UI.

## Consequences
- Drops htmx/Jinja/templates and Playwright-against-htmx from the earlier plan.
- The rich-interaction surfaces become feasible and testable (Vitest/jsdom +
  Playwright).
- Two stacks to maintain; the seam (ADR 0003) keeps them decoupled.
