import type { Metadata } from "next";
import Link from "next/link";

import { GradientOrbs } from "@/components/shared/backgrounds";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Welcome",
  path: "/kiosk",
  noindex: true,
});

export default function KioskWelcomePage() {
  return (
    <section className="relative isolate flex min-h-screen flex-col items-center justify-center overflow-hidden px-6">
      <GradientOrbs className="opacity-70" />
      <div className="relative z-10 max-w-xl space-y-6 text-center">
        <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
          Bytloop
        </p>
        <h1 className="text-5xl font-semibold tracking-tight">
          Tap to start
        </h1>
        <p className="text-base text-muted-foreground">
          Pick from the menu, pay, and grab your receipt.
        </p>
        <div className="pt-4">
          <Button asChild size="lg" className="h-16 px-10 text-lg">
            <Link href="/kiosk/shop">Start order</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
