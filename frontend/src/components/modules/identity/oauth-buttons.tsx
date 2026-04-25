"use client";

import { Github } from "lucide-react";

import { Button } from "@/components/shared/ui/button";
import { cn } from "@/lib/utils/cn";
import { AuthMethod } from "@/lib/stores/last-auth-method";

import { LastUsedBadge } from "./last-used-badge";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function oauthStart(provider: "google" | "github"): string {
  return `${API_BASE}/auth/${provider}/start`;
}

const oauthBtnClass = cn(
  "h-auto w-full min-w-0 min-h-11 border-zinc-600/80 bg-zinc-800/50 px-2 text-zinc-100 shadow-sm",
  "hover:border-primary/50 hover:bg-zinc-800/90 hover:text-white",
);

export function OAuthButtons() {
  return (
    <div className="grid grid-cols-2 gap-2.5">
      <Button asChild variant="outline" size="lg" className={oauthBtnClass}>
        <a
          href={oauthStart("google")}
          className="flex min-w-0 flex-col items-center justify-center gap-1 py-2.5 text-sm"
          aria-label="Continue with Google"
        >
          <GoogleIcon />
          <span className="text-center font-medium">Google</span>
          <LastUsedBadge method={AuthMethod.GOOGLE} />
        </a>
      </Button>
      <Button asChild variant="outline" size="lg" className={oauthBtnClass}>
        <a
          href={oauthStart("github")}
          className="flex min-w-0 flex-col items-center justify-center gap-1 py-2.5 text-sm"
          aria-label="Continue with GitHub"
        >
          <Github size={16} aria-hidden="true" />
          <span className="text-center font-medium">GitHub</span>
          <LastUsedBadge method={AuthMethod.GITHUB} />
        </a>
      </Button>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M12.48 10.92v3.28h7.84c-.24 1.84-.85 3.18-1.73 4.1-1.02 1.1-2.62 2.3-5.43 2.3-4.53 0-8.03-3.64-8.03-8.17s3.5-8.17 8.03-8.17c2.53 0 4.26 1 5.42 2.07l2.3-2.3C18.67 1.5 16.35.5 13.17.5 6.95.5 1.88 5.6 1.88 12s5.07 11.5 11.29 11.5c3.35 0 5.85-1.1 7.82-3.17 2.04-2.03 2.68-4.9 2.68-7.18 0-.73-.07-1.4-.17-2.23H12.48z"
      />
    </svg>
  );
}
