"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/shared/ui/badge";
import { type AuthMethod, getLastAuthMethod } from "@/lib/stores/last-auth-method";

type LastUsedBadgeProps = {
  readonly method: AuthMethod;
};

/**
 * Displays "Last used" next to the auth method the user last succeeded with.
 * Persists in localStorage per docs/PLAN.md §11.
 */
export function LastUsedBadge({ method }: LastUsedBadgeProps) {
  const [last, setLast] = useState<AuthMethod | null>(null);

  useEffect(() => {
    setLast(getLastAuthMethod());
  }, []);

  if (last !== method) return null;
  return (
    <Badge variant="secondary" className="ml-2 text-[10px]">
      Last used
    </Badge>
  );
}
