import { resolve } from "node:path";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": resolve(__dirname, ".") },
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
