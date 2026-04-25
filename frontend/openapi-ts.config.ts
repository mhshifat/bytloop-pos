import { defineConfig } from "@hey-api/openapi-ts";

/**
 * Configuration for `pnpm generate:api`.
 *
 * Actual invocation is via scripts/generate-api-client.ps1 which injects the
 * URL (defaulting to http://localhost:8000/openapi.json).
 */
export default defineConfig({
  input: process.env.OPENAPI_INPUT ?? "http://localhost:8000/openapi.json",
  output: {
    path: "src/lib/api-client/generated",
    format: "prettier",
    lint: "eslint",
  },
  plugins: [
    {
      name: "@hey-api/client-fetch",
      runtimeConfigPath: "./src/lib/api-client/client-config.ts",
    },
    "@hey-api/schemas",
    { name: "@hey-api/transformers", dates: true },
  ],
});
