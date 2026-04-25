"use client";

import { AlertCircle } from "lucide-react";

import type { ApiError } from "@/lib/api/error";
import { cn } from "@/lib/utils/cn";

import { CopyIdButton } from "./copy-id-button";

type InlineErrorProps = {
  readonly error: ApiError;
  readonly className?: string;
};

/**
 * Form-level / section-level error surface. Never renders stacktrace or internal data.
 */
export function InlineError({ error, className }: InlineErrorProps) {
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col gap-2 rounded-md border border-red-500/30 bg-red-500/5 p-3 text-sm",
        className,
      )}
    >
      <div className="flex items-start gap-2">
        <AlertCircle size={16} aria-hidden="true" className="mt-0.5 shrink-0 text-red-400" />
        <p className="text-red-100">{error.message}</p>
      </div>
      <CopyIdButton correlationId={error.correlationId} className="pl-6" />
    </div>
  );
}
