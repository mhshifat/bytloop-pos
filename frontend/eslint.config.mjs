import { FlatCompat } from "@eslint/eslintrc";
import { dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({ baseDirectory: __dirname });

const config = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    rules: {
      // Strict — docs/PLAN.md §5 Coding rules
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/consistent-type-imports": [
        "error",
        { prefer: "type-imports" },
      ],
      "no-console": ["warn", { allow: ["warn", "error"] }],

      // Enum display rule — docs/PLAN.md §13
      // Forbid rendering bare identifiers of type enum as JSX text.
      // (Team additionally relies on <EnumSelect>, <EnumBadge>, <EntityLabel>.)
      "no-restricted-syntax": [
        "warn",
        {
          selector:
            "JSXExpressionContainer > Identifier[name=/^(status|type|kind|category|role|state)$/]",
          message:
            "Do not render raw enum values. Use <EnumBadge>, <EnumSelect>, or a useXxxLabel() hook from src/lib/enums/.",
        },
      ],
    },
  },
  {
    ignores: [
      "node_modules/**",
      ".next/**",
      "out/**",
      "coverage/**",
      "playwright-report/**",
      "src/lib/api-client/generated/**",
    ],
  },
];

export default config;
