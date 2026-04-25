"use client";

import { LayoutDashboard, LogOut, User } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  Avatar,
  AvatarFallback,
} from "@/components/shared/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/shared/ui/dropdown-menu";
import { logout } from "@/lib/api/auth";
import { useAuthStore } from "@/lib/stores/auth-store";
import { cn } from "@/lib/utils/cn";

export type AppHeaderUserProps = {
  readonly email: string;
  readonly firstName: string;
  readonly lastName: string;
};

function initials(
  firstName: string,
  lastName: string,
  email: string
): string {
  const a = firstName?.trim().charAt(0) ?? "";
  const b = lastName?.trim().charAt(0) ?? "";
  if (a && b) return `${a}${b}`.toUpperCase();
  if (a) return a.toUpperCase();
  const fromEmail = email?.charAt(0) ?? "";
  if (fromEmail) return fromEmail.toUpperCase();
  return "?";
}

function displayName(
  firstName: string,
  lastName: string,
  email: string
): string {
  const full = `${firstName} ${lastName}`.trim();
  if (full) return full;
  return email;
}

export function AppHeaderUser({
  email,
  firstName,
  lastName,
}: AppHeaderUserProps) {
  const router = useRouter();
  const clear = useAuthStore((s) => s.clear);
  const name = displayName(firstName, lastName, email);
  const ini = initials(firstName, lastName, email);

  const onSignOut = async () => {
    try {
      await logout();
    } finally {
      clear();
      router.push("/login");
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className={cn(
          "flex h-10 max-w-full min-w-0 items-center gap-2.5 rounded-full border-0 bg-transparent pl-3 pr-1.5 sm:pl-4",
          "shadow-none ring-0 outline-none transition-colors duration-200",
          "hover:bg-white/[0.07]",
          "data-[state=open]:bg-white/10",
          "focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-0"
        )}
        aria-label="Account menu"
      >
        <div className="hidden min-w-0 max-w-44 flex-1 text-left sm:block sm:max-w-48">
          <p className="truncate text-left text-sm font-medium leading-tight text-zinc-100">
            {name}
          </p>
          <p className="hidden truncate text-left text-xs leading-tight text-zinc-500 md:block">
            {email}
          </p>
        </div>
        <Avatar
          size="lg"
          className="shrink-0 border-0 shadow-none ring-0"
        >
          <AvatarFallback className="bg-linear-to-br from-indigo-500/55 to-violet-600/50 text-sm font-semibold text-zinc-50">
            {ini}
          </AvatarFallback>
        </Avatar>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        className="w-56"
        sideOffset={8}
      >
        <DropdownMenuLabel className="font-normal">
          <p className="text-sm font-medium text-foreground leading-none">
            {name}
          </p>
          <p
            className="mt-1.5 truncate text-xs font-normal text-muted-foreground"
            title={email}
          >
            {email}
          </p>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/dashboard" className="flex cursor-pointer items-center gap-2">
            <LayoutDashboard size={14} aria-hidden />
            Dashboard
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/profile" className="flex cursor-pointer items-center gap-2">
            <User size={14} aria-hidden />
            Profile
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="text-destructive focus:text-destructive"
          onClick={() => {
            void onSignOut();
          }}
        >
          <LogOut size={14} aria-hidden />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
