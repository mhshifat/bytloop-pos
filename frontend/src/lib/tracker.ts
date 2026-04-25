/**
 * Analytics tracker — thin wrapper around the provider so we can swap
 * PostHog → Mixpanel → GA4 by touching only this file. See docs/PLAN.md §14.
 *
 * NO-OP until `NEXT_PUBLIC_POSTHOG_KEY` is set, so local dev and CI don't
 * send data and don't throw when the provider is absent.
 */

type EventProps = Readonly<Record<string, string | number | boolean | null>>;

type TrackerClient = {
  readonly identify: (userId: string, traits?: EventProps) => void;
  readonly track: (event: string, props?: EventProps) => void;
  readonly page: (name?: string, props?: EventProps) => void;
  readonly reset: () => void;
};

const NOOP: TrackerClient = {
  identify: () => undefined,
  track: () => undefined,
  page: () => undefined,
  reset: () => undefined,
};

let client: TrackerClient = NOOP;

type PostHogLite = {
  init: (key: string, config: { api_host: string; capture_pageview: boolean }) => void;
  identify: (userId: string, traits?: EventProps) => void;
  capture: (event: string, props?: EventProps) => void;
  reset: () => void;
};

export function initTracker(): void {
  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY;
  if (!key || typeof window === "undefined") return;

  // Dynamic import so the bundle cost is only paid when analytics is enabled.
  void import("posthog-js").then((mod) => {
    const ph = mod.default as unknown as PostHogLite;
    ph.init(key, {
      api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://us.i.posthog.com",
      capture_pageview: false, // handled manually via `page()`
    });
    client = {
      identify: (userId, traits) => ph.identify(userId, traits),
      track: (event, props) => ph.capture(event, props),
      page: (name, props) =>
        ph.capture("$pageview", { $current_url: name ?? "", ...(props ?? {}) }),
      reset: () => ph.reset(),
    };
  });
}

export const tracker: TrackerClient = {
  identify: (userId, traits) => client.identify(userId, traits),
  track: (event, props) => client.track(event, props),
  page: (name, props) => client.page(name, props),
  reset: () => client.reset(),
};
