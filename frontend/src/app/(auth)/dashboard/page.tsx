import type { Metadata } from "next";

import { DashboardStats } from "@/components/modules/reporting/dashboard-stats";
import { LowStockCard } from "@/components/modules/reporting/low-stock-card";
import { PaymentBreakdownCard } from "@/components/modules/reporting/payment-breakdown-card";
import { RecentOrdersCard } from "@/components/modules/reporting/recent-orders-card";
import { SalesChart } from "@/components/modules/reporting/sales-chart";
import { TopProductsCard } from "@/components/modules/reporting/top-products-card";
import { getCurrentUser } from "@/lib/auth";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Dashboard",
  path: "/dashboard",
  noindex: true,
});

export default async function DashboardPage() {
  const user = await getCurrentUser();

  return (
    <section className="space-y-6">
      <div className="relative isolate overflow-hidden rounded-2xl border border-zinc-600/50 bg-zinc-900/90 p-8 shadow-2xl shadow-black/50 ring-1 ring-white/5 backdrop-blur sm:p-10">
        <div className="relative z-10 space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">Welcome</p>
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-50">
            {user ? `Hello, ${user.firstName}` : "Hello"}
          </h1>
          <p className="text-sm text-zinc-400">
            Your workspace is ready. Open the POS terminal or browse your catalog.
          </p>
        </div>
      </div>

      <DashboardStats />

      <SalesChart />

      <div className="grid gap-4 md:grid-cols-2">
        <RecentOrdersCard />
        <LowStockCard />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <TopProductsCard />
        <PaymentBreakdownCard />
      </div>
    </section>
  );
}
