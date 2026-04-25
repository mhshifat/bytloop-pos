"use client";

import Link from "next/link";
import { AlertTriangle, CloudOff, RefreshCw } from "lucide-react";

import { useOfflineStatus } from "@/lib/hooks/use-offline-status";

/**
 * Sticky status banner — only rendered when something is worth surfacing.
 *
 * Three states:
 *   - offline: red, "Taking sales offline — they'll sync when you're back."
 *   - online + pending > 0: amber, "Syncing N queued items."
 *   - online + dead-lettered > 0: red, "N failed — needs attention."
 */
export function OfflineBanner() {
  const { online, pending, deadLettered } = useOfflineStatus();

  if (online && pending === 0 && deadLettered === 0) return null;

  let tone: "warn" | "danger" = "warn";
  let icon = <RefreshCw size={14} className="animate-spin" aria-hidden="true" />;
  let message = "";
  let linkLabel: string | null = null;

  if (!online) {
    tone = "danger";
    icon = <CloudOff size={14} aria-hidden="true" />;
    message =
      pending > 0
        ? `Offline — ${pending} queued ${pending === 1 ? "sale" : "sales"} will sync when you reconnect.`
        : "Offline — sales will be queued locally.";
  } else if (deadLettered > 0) {
    tone = "danger";
    icon = <AlertTriangle size={14} aria-hidden="true" />;
    message = `${deadLettered} queued ${
      deadLettered === 1 ? "mutation" : "mutations"
    } failed and need attention.`;
    linkLabel = "Review";
  } else {
    message = `Syncing ${pending} queued ${
      pending === 1 ? "item" : "items"
    }…`;
  }

  const toneClasses =
    tone === "danger"
      ? "border-red-500/50 bg-red-500/10 text-red-200"
      : "border-amber-500/50 bg-amber-500/10 text-amber-200";

  return (
    <div
      role="status"
      aria-live="polite"
      className={`sticky top-0 z-30 flex items-center justify-center gap-2 border-b px-4 py-1.5 text-xs ${toneClasses}`}
    >
      {icon}
      <span>{message}</span>
      {linkLabel ? (
        <Link href="/ops/offline-queue" className="underline underline-offset-2">
          {linkLabel}
        </Link>
      ) : null}
    </div>
  );
}
