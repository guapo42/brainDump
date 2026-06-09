import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,

  // Allow intentionally-unused args/vars when prefixed with `_` (e.g. interface
  // stubs that must keep a parameter name for documentation).
  {
    files: ["**/*.{ts,tsx}"],
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "warn",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_", caughtErrorsIgnorePattern: "^_" },
      ],
    },
  },

  // --- Determinism: pure-logic dirs may not touch the clock/RNG or cast through
  // `unknown` (CLAUDE.md Part VII). Effects own the clock; logic takes `now`. ---
  {
    files: ["engine/**/*.{ts,tsx}", "domain/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-properties": [
        "error",
        { object: "Date", property: "now", message: "Pure logic must take `now` as a parameter." },
        { object: "Math", property: "random", message: "Inject a seeded RNG; no Math.random in pure logic." },
        { object: "performance", property: "now", message: "Pure logic must take time as a parameter." },
      ],
      "no-restricted-globals": [
        "error",
        { name: "setInterval", message: "Timers belong in hooks, not pure logic." },
        { name: "setTimeout", message: "Timers belong in hooks, not pure logic." },
      ],
      "no-restricted-syntax": [
        "error",
        { selector: "NewExpression[callee.name='Date']", message: "Pure logic must take `now` as a parameter, not `new Date()`." },
        { selector: "TSAsExpression > TSUnknownKeyword", message: "No `as unknown as` — narrow with a runtime type guard." },
      ],
    },
  },

  // --- Boundary: app surfaces reach the backend ONLY via the IntelligenceService
  // factory, never a concrete adapter or backend code (CLAUDE.md Part III). ---
  {
    files: ["app/**/*.{ts,tsx}", "components/**/*.{ts,tsx}", "hooks/**/*.{ts,tsx}", "stores/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["**/services/intelligence/braindump*", "@/services/intelligence/braindump*"],
              message: "Reach the backend through getIntelligence(), not the concrete BrainDump adapter.",
            },
            {
              group: ["**/services/intelligence/local*", "@/services/intelligence/local*"],
              message: "Reach the backend through getIntelligence(), not the concrete Local adapter.",
            },
            {
              group: ["**/backend/**", "**/../backend/**"],
              message: "The frontend must not import backend code.",
            },
          ],
        },
      ],
    },
  },

  // Override default ignores of eslint-config-next.
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
