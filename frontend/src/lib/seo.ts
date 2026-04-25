/**
 * SEO single source of truth.
 *
 * Every page MUST compose its metadata via `buildMetadata()` — no inline
 * `title` / `description` / `openGraph` objects scattered across the app.
 *
 * See docs/PLAN.md §13 "SEO single source of truth".
 */

import type { Metadata } from "next";

const SITE_NAME = "Bytloop POS";
const DEFAULT_DESCRIPTION =
  "Multi-tenant SaaS POS for retail, food & beverage, hospitality, services, and specialty businesses.";
const APP_URL = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";

export type BuildMetadataInput = {
  readonly title?: string;
  readonly description?: string;
  readonly path?: string;
  readonly image?: string;
  readonly noindex?: boolean;
};

export function buildMetadata(input: BuildMetadataInput = {}): Metadata {
  const {
    title,
    description = DEFAULT_DESCRIPTION,
    path = "/",
    image,
    noindex = false,
  } = input;

  const fullTitle = title ? `${title} — ${SITE_NAME}` : SITE_NAME;
  const url = new URL(path, APP_URL).toString();

  return {
    title: fullTitle,
    description,
    metadataBase: new URL(APP_URL),
    /**
     * Prefer the vector mark for rel=icon (no raster matting / “grey frame” from PNG exports).
     * PNGs remain as fallbacks + for Apple / legacy.
     */
    icons: {
      icon: [
        { url: "/brand/bytloop-mark.svg", type: "image/svg+xml" },
        { url: "/icon-192.png", type: "image/png", sizes: "192x192" },
        { url: "/icon-512.png", type: "image/png", sizes: "512x512" },
      ],
      apple: [{ url: "/apple-touch-icon.png", type: "image/png", sizes: "180x180" }],
    },
    alternates: { canonical: url },
    robots: noindex ? { index: false, follow: false } : { index: true, follow: true },
    openGraph: {
      siteName: SITE_NAME,
      title: fullTitle,
      description,
      url,
      ...(image ? { images: [{ url: image }] } : {}),
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title: fullTitle,
      description,
      ...(image ? { images: [image] } : {}),
    },
  };
}
