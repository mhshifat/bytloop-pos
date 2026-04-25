"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { activate } from "@/lib/api/auth";
import { isApiError } from "@/lib/api/error";

type ActivateClientProps = {
  readonly token: string;
};

export function ActivateClient({ token }: ActivateClientProps) {
  const router = useRouter();

  const mutation = useMutation({
    mutationFn: (t: string) => activate(t),
    onSuccess: () => router.push("/login"),
  });

  useEffect(() => {
    mutation.mutate(token);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (mutation.isPending || mutation.isIdle) {
    return (
      <>
        <h1 className="text-2xl font-semibold">Activating…</h1>
        <p className="mt-2 text-sm text-[var(--color-muted)]">
          Verifying your activation link.
        </p>
      </>
    );
  }

  if (mutation.isError && isApiError(mutation.error)) {
    return (
      <div className="space-y-4">
        <InlineError error={mutation.error} />
        <Button onClick={() => mutation.mutate(token)} variant="outline" size="lg">
          Try again
        </Button>
      </div>
    );
  }

  return (
    <>
      <h1 className="text-2xl font-semibold">Account activated</h1>
      <p className="mt-2 text-sm text-[var(--color-muted)]">Redirecting to sign in…</p>
    </>
  );
}
