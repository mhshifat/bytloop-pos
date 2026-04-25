"use client";

import { useEffect } from "react";

import { apiFetch } from "@/lib/api/fetcher";

/**
 * Capture UTM parameters from the current URL and fire-and-forget a
 * ``POST /campaign-touches`` so the attribution report has data.
 *
 * Deduped per tab per hour via sessionStorage — the backend also rate-
 * limits, but no point hammering it from a reload loop.
 *
 * Fails silently: attribution is a nice-to-have, not a critical path.
 * A failed touch must never interfere with the user's actual task.
 */

const DEDUPE_KEY = "bytloop-utm-dedupe";
const DEDUPE_TTL_MS = 1000 * 60 * 60; // 1 hour — captures "same session" re-navigations

type UtmFields = {
  source: string | null;
  medium: string | null;
  campaign: string | null;
};

function readUtms(): UtmFields | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  const source = params.get("utm_source");
  const medium = params.get("utm_medium");
  const campaign = params.get("utm_campaign");
  if (!source && !medium && !campaign) return null;
  return { source, medium, campaign };
}

function channelFromUtms(utms: UtmFields): string {
  // "channel" is our canonical name — combine source+medium so
  // "google/cpc" and "google/organic" are distinguishable.
  const parts = [utms.source, utms.medium].filter(Boolean);
  return parts.length ? parts.join("/") : "unknown";
}

function alreadyCaptured(key: string): boolean {
  if (typeof sessionStorage === "undefined") return false;
  try {
    const raw = sessionStorage.getItem(DEDUPE_KEY);
    if (!raw) return false;
    const data = JSON.parse(raw) as Record<string, number>;
    const ts = data[key];
    return typeof ts === "number" && Date.now() - ts < DEDUPE_TTL_MS;
  } catch {
    return false;
  }
}

function markCaptured(key: string): void {
  if (typeof sessionStorage === "undefined") return;
  try {
    const raw = sessionStorage.getItem(DEDUPE_KEY);
    const data = (raw ? JSON.parse(raw) : {}) as Record<string, number>;
    data[key] = Date.now();
    sessionStorage.setItem(DEDUPE_KEY, JSON.stringify(data));
  } catch {
    // Quota exceeded etc. — just skip.
  }
}

export function useUtmCapture(options: {
  readonly tenantSlug: string | null;
  readonly customerId?: string | null;
}): void {
  const { tenantSlug, customerId = null } = options;

  useEffect(() => {
    if (!tenantSlug) return;
    const utms = readUtms();
    if (!utms) return;

    const channel = channelFromUtms(utms);
    // Dedupe on tenant+channel+campaign so the same user bouncing around
    // the app doesn't spam touches, but a real new campaign still fires.
    const dedupeKey = `${tenantSlug}::${channel}::${utms.campaign ?? ""}`;
    if (alreadyCaptured(dedupeKey)) return;

    const landing =
      typeof window !== "undefined"
        ? `${window.location.pathname}${window.location.search}`.slice(0, 255)
        : null;

    // Fire-and-forget — no await, no error surface.
    void apiFetch<void>("/campaign-touches", {
      method: "POST",
      json: {
        tenantSlug,
        channel,
        source: utms.source,
        medium: utms.medium,
        campaign: utms.campaign,
        landingPage: landing,
        customerId,
      },
    }).catch(() => {
      // Silent — attribution is best-effort.
    });

    markCaptured(dedupeKey);
  }, [tenantSlug, customerId]);
}
