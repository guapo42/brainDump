/**
 * App shell. Renders one of two surfaces (ADR 0008): a compact widget (current
 * priority + capture) and the full view. The Tauri desktop shell hosts the
 * compact surface as an always-on-top corner window and the full surface in a
 * main window; in the browser both render in one page. P0 is a placeholder.
 */
export function App() {
  return (
    <main className="p-6">
      <h1 className="text-lg font-semibold">The External Lobe</h1>
      <p className="text-sm opacity-70">scaffold — Vite + React, host-agnostic</p>
    </main>
  );
}
