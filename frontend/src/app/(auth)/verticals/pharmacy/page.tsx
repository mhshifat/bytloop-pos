import type { Metadata } from "next";

import { BatchesList } from "@/components/modules/pharmacy/batches-list";
import { BatchCreateForm } from "@/components/modules/pharmacy/batch-create-form";
import { ExpiringSoonCard } from "@/components/modules/pharmacy/expiring-soon-card";
import { PrescriptionForm } from "@/components/modules/pharmacy/prescription-form";
import { PrescriptionsList } from "@/components/modules/pharmacy/prescriptions-list";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Pharmacy",
  path: "/verticals/pharmacy",
  noindex: true,
});

export default function PharmacyPage() {
  return (
    <section className="space-y-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Pharmacy</h1>
          <p className="text-sm text-muted-foreground">
            Batch tracking, expiry visibility, prescription records.
          </p>
        </div>
        <PrescriptionForm />
      </header>

      <ExpiringSoonCard />

      <BatchCreateForm />
      <BatchesList />

      <div className="space-y-2">
        <h2 className="text-lg font-medium">Prescriptions</h2>
        <PrescriptionsList />
      </div>
    </section>
  );
}
