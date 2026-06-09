# ADR 0008 — Desktop shell (Tauri); host = Vite SPA

**Status:** accepted · **Date:** 2026-06-09 · **Amends:** ADR 0001 (host only)

## Context
The builder identified that a browser tab is itself friction: capture means
"find browser → find tab → focus → type," which blows the <3s zero-friction
principle (P1) and loses to whatever app is already on screen. For a daily-driver
ADHD tool, ambient presence may be *the* feature that makes the rest get used.
A browser tab cannot float always-on-top over other apps or be summoned by a
global hotkey.

## Decision
**Package the app as a native desktop app with Tauri** (Rust + the OS webview),
reusing the same React code:
- an **always-on-top, borderless corner widget** window (current priority +
  capture input),
- a **global hotkey** to summon capture from any app (the real <3s entry),
- a **system tray** icon,
- a **second main window** for the full view ("click to open the bigger view").

**Host = Vite + React SPA** (not Next.js). A local-first, single-user desktop app
has no SSR/SEO needs; Vite is the simpler, cleaner Tauri target and drops the
App-Router server/client split. The React app stays **host-agnostic**: it runs in
a plain browser during development and inside Tauri in use.

**Design constraints adopted now (cheap, good even if we never ship Tauri):**
1. **Two surfaces** — a compact widget view and a full view — are first-class
   from P1/P3, not retrofitted.
2. **Summonable capture** — capture is invoked (hotkey/command), never navigated
   to.
3. **No browser-only API is load-bearing** — continue feature-detecting (Web
   Speech, AudioContext, etc.).

## Consequences
- The Tauri shell lands as a dedicated phase (~P3.5, after the capture + priority
  + focus core), possibly the moment daily use actually begins. Build the logic
  host-agnostic first; wrap when it's worth living in your corner.
- **Toolchain:** Rust is required at the shell phase only (not before).
- **macOS caveat:** Tauri uses WKWebView there, where the **Web Speech API is
  unavailable** → voice capture degrades to text (already required by P5/graceful
  degradation). Windows uses WebView2 (Chromium) where it works.
- **Networking:** from the Tauri webview, calls to the local LLM / backend use
  Tauri's HTTP capability (or configured allowlist) to avoid browser CORS; in
  browser dev, the local servers need CORS set (carry-forward).
- ADR 0001's React/local-first decision stands; only the host (Next → Vite) and
  the shell (browser → desktop) change. The `IntelligenceService` seam, stores,
  and Anchor logic are unaffected.
