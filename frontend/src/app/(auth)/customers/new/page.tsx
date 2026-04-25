import type { Metadata } from "next";
import Link from "next/link";

import { CustomerCreateForm } from "@/components/modules/customers/customer-create-form";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "New customer",
  path: "/customers/new",
  noindex: true,
});

export default function NewCustomerPage() {
  return (
    <section className="mx-auto max-w-2xl space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">New customer</h1>
        <p className="text-sm text-muted-foreground">
          Minimum: name + an email or phone to reach them.
        </p>
      </header>
      <CustomerCreateForm />
      <Button asChild variant="ghost" size="sm">
        <Link href="/customers">← Back to customers</Link>
      </Button>
    </section>
  );
}
