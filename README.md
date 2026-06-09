# Brain Dump × The External Lobe

A local-first ADHD executive-function cockpit. One product, two halves joined at a
single seam:

- **The External Lobe** (`/app`) — a local-first **Triple-Engine** app
  (Pilot → Translator → Anchor) in Vite + React, packaged as a **Tauri desktop
  app** (always-on-top corner widget + global-hotkey capture; ADR 0008). Fully
  usable offline.
- **Brain Dump** (`/backend`) — an *optional* Python intelligence service: ingests
  external sources (Jira first), maintains a Neo4j/Chroma knowledge graph, and
  pushes back enrichment. Makes the app *smarter*, never *functional*.

The seam is the **`IntelligenceService` port** — the client always runs on a local
stub; the backend is a drop-in adapter.

## Layout

```
app/        Vite + React frontend (local-first; Tauri shell at P3.5)
backend/    FastAPI intelligence service (optional)
specs/      design source of truth (00 overview → 07 TDD plan)
docs/       working pattern, manual acceptance, ADRs, retrospectives
fixtures/   recorded JSON shared by FE adapter tests + BE (from P4)
legacy/     the original prototype — reference only, do not extend
```

## Quick start

```bash
make setup     # install both stacks (uv + npm)
make check     # all fast lanes + separation checks (the green bar)
make dev       # run the frontend (backend optional)
make up        # start Neo4j + Chroma (Docker) — needed from later phases
```

The frontend test suite runs entirely offline on `LocalIntelligence`; you do not
need the backend, Docker, or an LLM to develop or test the app.

## LLM

Provider-neutral: any local **OpenAI-compatible** server works (Ollama or
llama.cpp), selected by `LLM_BASE_URL` + `LLM_MODEL` in `backend/.env` — never
hardcoded (see `docs/decisions/0005-llm-provider-deferred.md`).

## Where to start reading

`specs/00-overview.md` → `05-iterative-plan.md`, then `CLAUDE.md` (conventions)
and `docs/working_pattern.md` (phase rhythm). Current state: **Phase 0 complete**
(`docs/retrospectives/phase_00.md`).
