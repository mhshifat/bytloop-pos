import type { Metadata } from "next";

import { PluRegisterForm } from "@/components/modules/grocery/plu-register-form";
import { ScanPanel } from "@/components/modules/grocery/scan-panel";
import { WebSerialScalePanel } from "@/components/modules/grocery/web-serial-scale-panel";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Grocery",
  path: "/verticals/grocery",
  noindex: true,
});

export default function GroceryPage() {
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Grocery</h1>
        <p className="text-sm text-muted-foreground">
          Register PLU codes, set weighable pricing, and test the scanner. Optional: pilot a
          USB scale via Web Serial in Chrome or Edge.
        </p>
      </header>
      <WebSerialScalePanel />
      <ScanPanel />
      <PluRegisterForm />
    </section>
  );
}
