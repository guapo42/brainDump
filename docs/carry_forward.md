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
