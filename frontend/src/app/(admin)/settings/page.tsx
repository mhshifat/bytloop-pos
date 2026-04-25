import type { Metadata } from "next";

import { SettingsTabs } from "@/components/modules/admin/settings-tabs";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Settings",
  path: "/settings",
  noindex: true,
});

export default function SettingsPage() {
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Workspace, brand, catalog structure, and pricing — use the tabs below.
        </p>
      </header>
      <SettingsTabs />
    </section>
  );
}
