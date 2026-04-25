"use client";

import { Check, Copy } from "lucide-react";
import { useCallback, useState } from "react";

import { cn } from "@/lib/utils/cn";

type CopyIdButtonProps = {
  readonly correlationId: string;
  readonly className?: string;
};

/**
 * One-click copy for a correlation ID. Users paste this into support chat
 * so the team can search logs instantly. See docs/PLAN.md §12.
 */
export function CopyIdButton({ correlationId, className }: CopyIdButtonProps) {
  const [copied, setCopied] = useState(false);

  const onCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(correlationId);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API can fail (permissions, http). The user can still read
      // the ID from the adjacent monospace text node.
    }
  }, [correlationId]);

  return (
    <div className={cn("inline-flex items-center gap-2 text-xs", className)}>
      <code
        aria-label="Error correlation ID"
        className="rounded bg-black/20 px-1.5 py-0.5 font-mono text-[11px] tracking-tight"
      >
        {correlationId}
      </code>
      <button
        type="button"
        onClick={onCopy}
        aria-label={copied ? "Copied correlation ID" : "Copy correlation ID"}
        className="inline-flex h-6 w-6 items-center justify-center rounded hover:bg-white/5 focus-visible:outline"
      >
        {copied ? (
          <Check size={13} aria-hidden="true" />
        ) : (
          <Copy size={13} aria-hidden="true" />
        )}
      </button>
      {copied ? <span className="text-[11px] opacity-70">Copied</span> : null}
    </div>
  );
}
