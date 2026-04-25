"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { AlertTriangle } from "lucide-react";

import type { ApiError } from "@/lib/api/error";

import { CopyIdButton } from "./copy-id-button";

type ErrorDialogProps = {
  readonly error: ApiError | null;
  readonly open: boolean;
  readonly onOpenChange: (open: boolean) => void;
};

/**
 * Blocking error dialog for catastrophic / confirmation-required failures.
 */
export function ErrorDialog({ error, open, onOpenChange }: ErrorDialogProps) {
  return (
    <Dialog.Root open={open && error !== null} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-2xl focus:outline-none">
          <div className="flex items-start gap-3">
            <AlertTriangle size={22} aria-hidden="true" className="mt-0.5 shrink-0 text-amber-400" />
            <div className="flex-1 space-y-3">
              <Dialog.Title className="text-base font-semibold">
                Something went wrong
              </Dialog.Title>
              <Dialog.Description className="text-sm text-[var(--color-muted)]">
                {error?.message}
              </Dialog.Description>
              {error ? <CopyIdButton correlationId={error.correlationId} /> : null}
            </div>
          </div>
          <div className="mt-6 flex justify-end">
            <button
              type="button"
              onClick={() => onOpenChange(false)}
              className="rounded-md bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-[var(--color-accent-fg)]"
            >
              Dismiss
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
