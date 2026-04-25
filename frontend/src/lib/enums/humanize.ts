/**
 * Dev-only: convert `SHIPPING_ADDRESS` → `Shipping address`.
 *
 * NEVER use this for user-visible UI — use the label hooks from
 * `src/lib/enums/<enum>.ts` instead, backed by next-intl translations.
 * This exists for logs and devtools only.
 *
 * See docs/PLAN.md §13 Enum display rule.
 */

export function humanize(value: string): string {
  if (!value) return value;
  const spaced = value
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .toLowerCase();
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}
