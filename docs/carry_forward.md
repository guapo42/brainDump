# Carry-Forward

Live list of deferrals. Each item: origin → acceptance criteria. Remove when done.

- **`BrainDumpIntelligence` adapter** (origin P0 seam) → P4: implement the
  `IntelligenceService` against the FastAPI API; verified against recorded
  `/fixtures`.
- **Generated seam types** (origin ADR 0003) → when the API exposes OpenAPI:
  generate TS types (`openapi-typescript`) and check against `/fixtures` so FE/BE
  can't diverge.
- **`jest-axe` a11y in the component-test template** (origin P0 recommendation) →
  P3, when the first components land.
- **Sim seed fixture export** (origin specs/04 §12.5) → P4/P8: export the 52-week
  sim scenario as offline demo + Playwright data.
- **Finalize LLM provider** (origin ADR 0005) → after research: pick Ollama vs
  llama.cpp; record a follow-up ADR; no call-site changes (config only).
- **Boundary linter upgrade** (origin P0) → consider `dependency-cruiser` if the
  ESLint `no-restricted-imports` rules prove too coarse.
- **`make dev` smoke** (origin P0 retro) → run `npm run dev` and confirm the page
  renders with no console errors (not exercised in the P0 build container).
- **Next 16 / React 19 are bleeding-edge** (origin P0 scaffold) → by end of P2:
  either affirm (no ecosystem friction observed with Zustand/Framer
  Motion/Testing Library) or pin back to Next 15/React 18 while the surface is
  still small.
- **Browser → local LLM CORS** (origin plan review) → at P2 (Translator):
  browser calls to a local server need CORS — Ollama requires `OLLAMA_ORIGINS`,
  llama.cpp needs `llama-server` CORS flags. Verify both, document in
  `backend/.env.example` comments; the heuristic fallback must mask a CORS
  failure gracefully (it looks like "LLM down").
- **P5 tone-signal gap with real Jira data** (origin plan review, specs/04
  §9.2) → decide at P5 pre-flight: enrich Jira *comments* via LLM to recover
  follow-up/tone signals, or recalibrate the headline-demo criteria to
  mentions+overdue+priority. Until then the full formula is validated by the
  sim only.
