import Link from "next/link";
import type { ReactNode } from "react";

import { BytloopLogoMark } from "@/components/shared/brand/bytloop-logo";
import { AuroraWaves, GradientOrbs, GridParticles } from "@/components/shared/backgrounds";

type GuestAuthShellProps = {
  readonly children: ReactNode;
};

/**
 * Auth route wrapper — same surface / contrast / motion language as the public marketing page.
 */
export function GuestAuthShell({ children }: GuestAuthShellProps) {
  return (
    <div className="marketing-page fixed inset-0 z-0 flex min-h-0 flex-col overflow-hidden bg-background text-zinc-50">
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <GradientOrbs className="opacity-40" />
        <GridParticles />
        <AuroraWaves className="opacity-45" />
      </div>
      <header className="z-20 shrink-0 border-b border-zinc-800/70 bg-zinc-950/80 backdrop-blur-xl">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link
            href="/"
            className="flex items-center gap-2.5 font-semibold tracking-tight text-zinc-50"
          >
            <BytloopLogoMark className="h-8 w-8 shadow-md shadow-primary/20" />
            <span className="text-sm sm:text-base">Bytloop POS</span>
          </Link>
          <Link
            href="/"
            className="text-sm font-medium text-zinc-300 transition hover:text-white"
          >
            Home
          </Link>
        </div>
      </header>
      {/* flex-1 + min-h-0: fill viewport under header without min-height + padding overshooting 100dvh (which caused a useless body scroll) */}
      <div className="mx-auto flex min-h-0 w-full max-w-md flex-1 flex-col justify-center overflow-y-auto overscroll-y-contain px-4 py-4 sm:px-6 sm:py-6">
        <div className="w-full">
          <div className="rounded-2xl border border-zinc-600/50 bg-zinc-900/90 p-6 shadow-2xl shadow-black/50 ring-1 ring-white/5 backdrop-blur sm:p-8">
            {children}
          </div>
          <p className="mt-4 text-balance text-center text-xs leading-relaxed text-zinc-500 sm:mt-5">
            By continuing, you agree to our terms and privacy policy.
          </p>
        </div>
      </div>
    </div>
  );
}
