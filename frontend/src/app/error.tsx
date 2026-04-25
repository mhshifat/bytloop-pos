"use client";

import { useEffect } from "react";
import { ulid } from "ulid";

import { CopyIdButton } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";

type ErrorPageProps = {
  readonly error: Error & { readonly digest?: string };
  readonly reset: () => void;
};

export default function RouteError({ error, reset }: ErrorPageProps) {
  const correlationId = error.digest ?? `client_${ulid()}`;

  useEffect(() => {
    console.error("route_error", { correlationId, error });
  }, [correlationId, error]);

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-4 p-6 text-center">
      <h1 className="text-2xl font-semibold">Something went wrong</h1>
      <p className="text-sm text-muted-foreground">
        An unexpected error happened while rendering this page. You can share the ID
        below with support to speed up the fix.
      </p>
      <CopyIdButton correlationId={correlationId} />
      <div className="flex gap-2">
        <Button onClick={() => reset()}>Try again</Button>
        <Button asChild variant="outline">
          <a href="/dashboard">Back to dashboard</a>
        </Button>
      </div>
    </main>
  );
}
