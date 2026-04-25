import type { Metadata } from "next";

import { JobCreateForm } from "@/components/modules/garage/job-create-form";
import { JobsBoard } from "@/components/modules/garage/jobs-board";
import { VehicleCreateForm } from "@/components/modules/garage/vehicle-create-form";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Garage",
  path: "/verticals/garage",
  noindex: true,
});

export default function GaragePage() {
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Garage</h1>
        <p className="text-sm text-muted-foreground">Vehicles &amp; job cards.</p>
      </header>
      <VehicleCreateForm />
      <JobCreateForm />
      <JobsBoard />
    </section>
  );
}
