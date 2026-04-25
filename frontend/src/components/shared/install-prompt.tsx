"use client";

import { Download, X } from "lucide-react";

import { Button } from "@/components/shared/ui/button";
import { useInstallPrompt } from "@/lib/hooks/use-install-prompt";

export function InstallPrompt() {
  const { canInstall, promptInstall, dismiss } = useInstallPrompt();
  if (!canInstall) return null;

  return (
    <div
      role="dialog"
      aria-label="Install Bytloop POS"
      className="fixed bottom-4 right-4 z-40 flex max-w-sm items-start gap-3 rounded-lg border border-border bg-surface p-3 shadow-2xl"
    >
      <Download size={18} className="mt-0.5 text-primary" aria-hidden="true" />
      <div className="flex-1 text-sm">
        <p className="font-medium">Install Bytloop POS</p>
        <p className="text-xs text-muted-foreground">
          Runs in its own window, starts faster, works offline.
        </p>
        <div className="mt-2 flex gap-2">
          <Button size="sm" onClick={() => void promptInstall()}>
            Install
          </Button>
          <Button size="sm" variant="ghost" onClick={dismiss}>
            Not now
          </Button>
        </div>
      </div>
      <button
        type="button"
        aria-label="Dismiss"
        className="text-muted-foreground hover:text-foreground"
        onClick={dismiss}
      >
        <X size={14} />
      </button>
    </div>
  );
}
