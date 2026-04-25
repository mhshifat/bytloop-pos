/**
 * next-intl configuration.
 *
 * Locale is read from a cookie (`bytloop_locale`) with English as the default.
 * Adding a language = drop a new JSON in `frontend/messages/`.
 */

export const locales = ["en", "bn"] as const;
export type Locale = (typeof locales)[number];

export const DEFAULT_LOCALE: Locale = "en";
export const LOCALE_COOKIE = "bytloop_locale";

export function isLocale(value: string | undefined): value is Locale {
  return value === "en" || value === "bn";
}
