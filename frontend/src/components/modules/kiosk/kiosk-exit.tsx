"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";

/**
 * Staff exit — PIN check is intentionally client-side for the MVP. Kiosks
 * are assumed to run on locked hardware (`chromium --kiosk`) and the PIN
 * is a "won't let a customer back out" barrier, not a security boundary.
 *
 * Swap to a server call (``POST /auth/kiosk-unlock``) once that endpoint
 * exists and tenant owners can rotate the PIN from settings.
 */
const EXPECTED_PIN = process.env.NEXT_PUBLIC_KIOSK_EXIT_PIN ?? "1234";

export function KioskExit() {
  const router = useRouter();
  const [pin, setPin] = useState("");
  const [err, setErr] = useState<string | null>(null);

  return (
    <section className="flex min-h-screen items-center justify-center p-6">
      <form
        className="w-full max-w-sm space-y-4 rounded-lg border border-border bg-surface p-6"
        onSubmit={(e) => {
          e.preventDefault();
          if (pin === EXPECTED_PIN) {
            router.push("/dashboard");
          } else {
            setErr("Incorrect PIN.");
            setPin("");
          }
        }}
      >
        <header>
          <h1 className="text-xl font-semibold tracking-tight">Staff unlock</h1>
          <p className="text-sm text-muted-foreground">
            Enter the 4-digit PIN to leave kiosk mode.
          </p>
        </header>
        <div className="space-y-1.5">
          <Label htmlFor="kiosk-pin">PIN</Label>
          <Input
            id="kiosk-pin"
            type="password"
            inputMode="numeric"
            autoComplete="off"
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            autoFocus
            maxLength={8}
          />
        </div>
        {err ? <p className="text-sm text-red-400">{err}</p> : null}
        <div className="flex justify-between gap-2">
          <Button type="button" variant="ghost" onClick={() => router.push("/kiosk")}>
            Cancel
          </Button>
          <Button type="submit" disabled={pin.length === 0}>
            Unlock
          </Button>
        </div>
      </form>
    </section>
  );
}
