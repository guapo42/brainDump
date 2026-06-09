import { fileURLToPath } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const root = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { "@": root },
  },
  test: {
    // Node by default; opt into jsdom per-file via `// @vitest-environment jsdom`.
    environment: "node",
    setupFiles: ["./vitest.setup.ts"],
    globals: true,
    coverage: {
      provider: "v8",
      // Coverage gates apply to pure logic only (CLAUDE.md Part VIII §3).
      include: ["engine/**", "domain/**", "lib/**"],
      thresholds: { branches: 90, functions: 90, lines: 90, statements: 90 },
    },
  },
});
