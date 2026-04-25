import type { Metadata } from "next";
import Link from "next/link";

import { LtvCard } from "@/components/modules/ai/ltv-card";
import { CustomerDetail } from "@/components/modules/customers/customer-detail";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Customer",
  path: "/customers",
  noindex: true,
});

type PageProps = {
  readonly params: Promise<{ readonly customerId: string }>;
};

export default async function CustomerDetailPage({ params }: PageProps) {
  const { customerId } = await params;
  return (
    <section className="mx-auto max-w-3xl space-y-6">
      <Button asChild variant="ghost" size="sm">
        <Link href="/customers">← Back to customers</Link>
      </Button>
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Customer</h1>
      </header>
      <LtvCard customerId={customerId} />
      <CustomerDetail customerId={customerId} />
    </section>
  );
}
