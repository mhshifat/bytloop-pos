import type { Metadata } from "next";
import Link from "next/link";
import { Plus } from "lucide-react";

import { CustomersList } from "@/components/modules/customers/customers-list";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Customers",
  path: "/customers",
  noindex: true,
});

export default function CustomersPage() {
  return (
    <section className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Customers</h1>
          <p className="text-sm text-muted-foreground">Your workspace contacts.</p>
        </div>
        <Button asChild>
          <Link href="/customers/new" className="flex items-center gap-2">
            <Plus size={14} /> New customer
          </Link>
        </Button>
      </header>
      <CustomersList />
    </section>
  );
}
