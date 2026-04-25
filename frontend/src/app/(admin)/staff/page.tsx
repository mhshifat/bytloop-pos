import type { Metadata } from "next";

import { StaffInviteDialog } from "@/components/modules/admin/staff-invite-dialog";
import { StaffList } from "@/components/modules/admin/staff-list";
import { getCurrentUser } from "@/lib/auth";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Staff",
  path: "/staff",
  noindex: true,
});

export default async function StaffPage() {
  const user = await getCurrentUser();
  return (
    <section className="space-y-6 p-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Staff</h1>
          <p className="text-sm text-muted-foreground">
            Invite teammates, update roles, and keep access tight.
          </p>
        </div>
        <StaffInviteDialog />
      </header>
      <StaffList currentUserId={user?.id ?? ""} />
    </section>
  );
}
