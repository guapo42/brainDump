import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist/**", "coverage/**"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,

  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: { globals: { ...globals.browser } },
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
    files: ["components/**/*.{ts,tsx}", "hooks/**/*.{ts,tsx}", "stores/**/*.{ts,tsx}", "App.tsx", "main.tsx"],
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
);
