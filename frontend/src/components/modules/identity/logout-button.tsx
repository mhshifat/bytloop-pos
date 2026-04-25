"use client";

import { LogOut } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/shared/ui/button";
import { logout } from "@/lib/api/auth";
import { useAuthStore } from "@/lib/stores/auth-store";

export function LogoutButton() {
  const router = useRouter();
  const clear = useAuthStore((s) => s.clear);

  const onLogout = async (): Promise<void> => {
    try {
      await logout();
    } finally {
      clear();
      router.push("/login");
    }
  };

  return (
    <Button variant="outline" onClick={onLogout}>
      <LogOut size={14} aria-hidden="true" /> Sign out
    </Button>
  );
}
