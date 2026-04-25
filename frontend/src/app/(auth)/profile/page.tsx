import type { Metadata } from "next";

import { ChangePasswordFormComponent } from "@/components/modules/identity/change-password-form";
import { LogoutButton } from "@/components/modules/identity/logout-button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared/ui/card";
import { getCurrentUser } from "@/lib/auth";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Profile",
  path: "/profile",
  noindex: true,
});

export default async function ProfilePage() {
  const user = await getCurrentUser();

  return (
    <section className="mx-auto w-full max-w-5xl space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Your profile</h1>
        <p className="text-sm text-muted-foreground">Manage your account.</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        {user ? (
          <Card className="lg:sticky lg:top-6 lg:self-start">
            <CardHeader>
              <CardTitle className="text-base">Account</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <Row label="Name" value={`${user.firstName} ${user.lastName}`.trim() || "—"} />
              <Row label="Email" value={user.email || "—"} />
              <Row label="Email verified" value={user.emailVerified ? "Yes" : "No"} />
              <Row label="Roles" value={user.roles.join(", ") || "—"} />
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Account</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              No user session found.
            </CardContent>
          </Card>
        )}

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Security</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">
                  Update your password to keep your account secure.
                </p>
              </div>
              <div className="mt-4">
                <ChangePasswordFormComponent />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Sign out</CardTitle>
            </CardHeader>
            <CardContent className="flex items-center justify-between gap-3">
              <p className="text-sm text-muted-foreground">
                Sign out of this browser session.
              </p>
              <LogoutButton />
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}

function Row({ label, value }: { readonly label: string; readonly value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span>{value}</span>
    </div>
  );
}
