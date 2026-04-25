"use client";

import { useCallback, useEffect, useState } from "react";

type BeforeInstallPromptEvent = Event & {
  readonly platforms: readonly string[];
  readonly userChoice: Promise<{ readonly outcome: "accepted" | "dismissed" }>;
  prompt(): Promise<void>;
};

const DISMISSED_KEY = "bytloop-install-dismissed-at";
const DISMISS_COOLDOWN_MS = 1000 * 60 * 60 * 24 * 14; // two weeks

/**
 * Chromium install-prompt capture. Users can dismiss for two weeks so we
 * don't nag — if they really want it later, the browser menu still works.
 */
export function useInstallPrompt(): {
  readonly canInstall: boolean;
  readonly promptInstall: () => Promise<void>;
  readonly dismiss: () => void;
} {
  const [event, setEvent] = useState<BeforeInstallPromptEvent | null>(null);
  const [canInstall, setCanInstall] = useState(false);

  useEffect(() => {
    const dismissedAt = Number(localStorage.getItem(DISMISSED_KEY) ?? "0");
    if (Date.now() - dismissedAt < DISMISS_COOLDOWN_MS) return;

    const handler = (e: Event) => {
      e.preventDefault();
      setEvent(e as BeforeInstallPromptEvent);
      setCanInstall(true);
    };
    window.addEventListener("beforeinstallprompt", handler as EventListener);
    return () =>
      window.removeEventListener("beforeinstallprompt", handler as EventListener);
  }, []);

  const promptInstall = useCallback(async () => {
    if (!event) return;
    await event.prompt();
    const result = await event.userChoice;
    setCanInstall(false);
    setEvent(null);
    if (result.outcome === "dismissed") {
      localStorage.setItem(DISMISSED_KEY, String(Date.now()));
    }
  }, [event]);

  const dismiss = useCallback(() => {
    localStorage.setItem(DISMISSED_KEY, String(Date.now()));
    setCanInstall(false);
    setEvent(null);
  }, []);

  return { canInstall, promptInstall, dismiss };
}
