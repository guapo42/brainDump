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
- **`make dev` smoke** (origin P0 retro) → run `npm run dev` (Vite) and confirm
  the page renders with no console errors (not exercised in the build container).
- **React 19 + Vite stack** (origin P0 scaffold; host switched to Vite per ADR
  0008) → by end of P2, affirm no ecosystem friction (Zustand, Framer Motion,
  Testing Library) while the surface is small.
- **Tauri toolchain (Rust)** (origin ADR 0008) → install at the **P3.5 shell
  phase** only; not needed before. Verify always-on-top + global-hotkey + tray on
  the target OS.
- **macOS WKWebView Web Speech** (origin ADR 0008) → at P3.5, confirm voice
  capture availability in the Tauri webview; ensure graceful text fallback when
  absent.
- **Local-LLM connectivity (CORS vs Tauri HTTP)** (origin plan review + ADR 0008)
  → at P2 (Translator) in browser dev, the local server needs CORS (Ollama
  `OLLAMA_ORIGINS`; llama.cpp `llama-server` flags). Inside Tauri (P3.5), prefer
  Tauri's HTTP capability to sidestep CORS. Either way the heuristic fallback must
  mask a connectivity failure gracefully (looks like "LLM down").
- **P5 tone-signal gap with real Jira data** (origin plan review, specs/04
  §9.2) → decide at P5 pre-flight: enrich Jira *comments* via LLM to recover
  follow-up/tone signals, or recalibrate the headline-demo criteria to
  mentions+overdue+priority. Until then the full formula is validated by the
  sim only.
