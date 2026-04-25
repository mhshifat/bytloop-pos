import type { ReactNode } from "react";

import { AskFab } from "@/components/shared/ask-fab";
import { AppHeaderUser } from "@/components/shared/layout/app-header-user";
import { AppShellBackground } from "@/components/shared/layout/app-shell-background";
import { AppSidebar } from "@/components/shared/layout/app-sidebar";
import { BrandProvider } from "@/components/shared/layout/brand-provider";
import { ThemeToggle } from "@/components/shared/layout/theme-toggle";
import { OfflineBanner } from "@/components/shared/offline-banner";
import { ShortcutsHelp } from "@/components/shared/shortcuts-help";
import { UtmCapture } from "@/components/shared/utm-capture";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/shared/ui/sidebar";
import type { CurrentUser } from "@/lib/auth";

type AuthenticatedAppShellProps = {
  readonly children: ReactNode;
  /** Logged-in user for the top bar (server layouts pass `getCurrentUser()`). */
  readonly user: Pick<CurrentUser, "email" | "firstName" | "lastName">;
};

/**
 * Shared chrome: gradient background, sidebar, top bar, scrollable main.
 * Used by `(auth)` and `(admin)` route groups so all app pages look the same.
 */
export function AuthenticatedAppShell({ children, user }: AuthenticatedAppShellProps) {
  return (
    <div className="app-admin relative min-h-svh bg-background text-foreground">
      <AppShellBackground />
      <BrandProvider>
        <UtmCapture />
        <SidebarProvider>
          <AppSidebar />
          <SidebarInset className="relative z-0 h-svh max-h-svh min-h-0 flex flex-col border-0 bg-background/95 shadow-none">
            <OfflineBanner />
            <header className="z-10 flex h-14 shrink-0 items-center gap-3 border-b border-zinc-800/70 bg-zinc-950/80 px-3 shadow-sm shadow-black/20 backdrop-blur-xl sm:px-4">
              <SidebarTrigger className="text-zinc-300" />
              <div className="ml-auto flex min-w-0 items-center gap-1.5 sm:gap-2">
                <ShortcutsHelp />
                <ThemeToggle />
                <AppHeaderUser
                  email={user.email}
                  firstName={user.firstName}
                  lastName={user.lastName}
                />
              </div>
            </header>
            <div className="relative z-0 flex min-h-0 w-full max-w-[1680px] flex-1 flex-col space-y-0 overflow-y-auto p-4 sm:p-6 lg:px-8">
              {children}
            </div>
          </SidebarInset>
          <AskFab />
        </SidebarProvider>
      </BrandProvider>
    </div>
  );
}
