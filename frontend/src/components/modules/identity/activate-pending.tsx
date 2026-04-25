"use client";

import { useMutation } from "@tanstack/react-query";
import { MailCheck } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { resendActivation } from "@/lib/api/auth";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";

const COOLDOWN_SECONDS = 300;
const STORAGE_KEY_PREFIX = "bytloop:resend_expires_at:";

type ActivatePendingProps = {
  readonly email: string;
};

function storageKey(email: string): string {
  return `${STORAGE_KEY_PREFIX}${email.toLowerCase()}`;
}

function loadRemaining(email: string): number {
  if (typeof window === "undefined") return 0;
  const raw = window.localStorage.getItem(storageKey(email));
  if (!raw) return 0;
  const expiresAt = Number.parseInt(raw, 10);
  if (Number.isNaN(expiresAt)) return 0;
  const remaining = Math.ceil((expiresAt - Date.now()) / 1000);
  return Math.max(0, remaining);
}

function persistCooldown(email: string, seconds: number): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(storageKey(email), String(Date.now() + seconds * 1000));
}

function formatMMSS(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${minutes}:${s.toString().padStart(2, "0")}`;
}

/**
 * Shows the post-signup activation prompt with a live 5-minute countdown
 * on the resend button. See docs/PLAN.md §11.
 */
export function ActivatePending({ email }: ActivatePendingProps) {
  const [remaining, setRemaining] = useState<number>(() => loadRemaining(email));
  const [sent, setSent] = useState(false);
  const [serverError, setServerError] = useState<ApiError | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startCountdown = useCallback(() => {
    if (intervalRef.current) return;
    intervalRef.current = setInterval(() => {
      setRemaining((prev) => {
        if (prev <= 1) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }, []);

  useEffect(() => {
    if (remaining > 0) startCountdown();
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [remaining, startCountdown]);

  const mutation = useMutation({
    mutationFn: () => resendActivation(email),
    onError: (err) => {
      if (isApiError(err)) {
        setServerError(err);
        // 429 from server includes cooldownRemainingSeconds in details.
        const detail = err.details as { cooldownRemainingSeconds?: number } | null;
        if (err.status === 429 && detail?.cooldownRemainingSeconds) {
          setRemaining(detail.cooldownRemainingSeconds);
          persistCooldown(email, detail.cooldownRemainingSeconds);
          startCountdown();
        }
      }
    },
    onSuccess: () => {
      setSent(true);
      setServerError(null);
      setRemaining(COOLDOWN_SECONDS);
      persistCooldown(email, COOLDOWN_SECONDS);
      startCountdown();
    },
  });

  const disabled = remaining > 0 || mutation.isPending;

  return (
    <div className="flex flex-col items-center gap-5 text-center">
      <div className="rounded-full bg-[var(--color-accent)]/10 p-4">
        <MailCheck className="text-[var(--color-accent)]" size={32} aria-hidden="true" />
      </div>
      <div className="space-y-1.5">
        <h1 className="text-2xl font-semibold">Check your email</h1>
        <p className="text-sm text-[var(--color-muted)]">
          We sent an activation link to <strong className="text-foreground">{email}</strong>.
          Click it to sign in.
        </p>
      </div>

      {sent ? (
        <p role="status" className="text-sm text-emerald-400">
          Activation email sent again. Please check your inbox.
        </p>
      ) : null}

      {serverError ? <InlineError error={serverError} /> : null}

      <Button
        onClick={() => {
          setServerError(null);
          setSent(false);
          mutation.mutate();
        }}
        disabled={disabled}
        size="lg"
      >
        {remaining > 0
          ? `Resend in ${formatMMSS(remaining)}`
          : mutation.isPending
            ? "Sending…"
            : "Resend activation email"}
      </Button>

      <p className="text-xs text-[var(--color-muted)]">
        Wrong email?{" "}
        <a href="/signup" className="underline">
          Sign up again
        </a>
      </p>
    </div>
  );
}
