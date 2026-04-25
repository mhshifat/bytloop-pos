import type { Metadata } from "next";

import { AuditLogList } from "@/components/modules/admin/audit-log-list";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Audit log",
  path: "/audit-log",
  noindex: true,
});

export default function AuditLogPage() {
  return (
    <section className="space-y-6 p-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Audit log</h1>
        <p className="text-sm text-muted-foreground">
          Every write, user-tagged and time-stamped.
        </p>
      </header>
      <AuditLogList />
    </section>
  );
}
