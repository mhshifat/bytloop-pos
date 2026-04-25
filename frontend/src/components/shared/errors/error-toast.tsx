"use client";

import { toast } from "sonner";

import type { ApiError } from "@/lib/api/error";

import { CopyIdButton } from "./copy-id-button";

/**
 * Show an error toast that includes a Copy-ID affordance. Wraps sonner.
 */
export function showErrorToast(error: ApiError): void {
  toast.error(error.message, {
    description: <CopyIdButton correlationId={error.correlationId} />,
    duration: 8000,
  });
}
