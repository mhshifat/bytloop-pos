"use client";

import { Menu, X } from "lucide-react";
import Link from "next/link";
import { useState, type MouseEvent } from "react";

import { BytloopLogoMark } from "@/components/shared/brand/bytloop-logo";
import { Button } from "@/components/shared/ui/button";
import { cn } from "@/lib/utils/cn";

const NAV: { href: string; label: string }[] = [
  { href: "#simplicity", label: "Why us" },
  { href: "#product", label: "Features" },
  { href: "#pos-types", label: "POS types" },
  { href: "#industries", label: "Sectors" },
  { href: "#workflow", label: "Workflow" },
  { href: "#faq", label: "FAQ" },
];

function scrollToHash(e: MouseEvent<HTMLAnchorElement>, href: string) {
  if (!href.startsWith("#")) return;
  e.preventDefault();
  const el = document.getElementById(href.slice(1));
  el?.scrollIntoView({ behavior: "smooth", block: "start" });
  window.history.pushState(null, "", href);
}

type MarketingNavProps = {
  readonly signedIn: boolean;
};

export function MarketingNav({ signedIn }: MarketingNavProps) {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-zinc-700/60 bg-zinc-950/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <a
          href="#hero"
          onClick={(e) => {
            setOpen(false);
            scrollToHash(e, "#hero");
          }}
          className="flex items-center gap-2.5 font-semibold tracking-tight text-zinc-50"
        >
          <BytloopLogoMark className="h-9 w-9 shadow-lg shadow-primary/20 ring-1 ring-white/15" />
          <span className="hidden sm:inline sm:text-base">Bytloop POS</span>
        </a>

        <nav
          className="hidden items-center gap-0.5 rounded-full border border-zinc-600/50 bg-zinc-900/50 p-1 md:flex"
          aria-label="Page sections"
        >
          {NAV.map((item) => (
            <a
              key={item.href}
              href={item.href}
              onClick={(e) => scrollToHash(e, item.href)}
              className="rounded-full px-3.5 py-2 text-sm font-medium text-zinc-200 transition hover:bg-zinc-800/80 hover:text-white"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-2 sm:flex">
          {signedIn ? (
            <Button
              asChild
              size="sm"
              className="font-semibold shadow-lg shadow-primary/25"
            >
              <Link href="/dashboard">Dashboard</Link>
            </Button>
          ) : (
            <>
              <Button
                asChild
                variant="ghost"
                size="sm"
                className="text-zinc-200 hover:bg-zinc-800 hover:text-white"
              >
                <Link href="/login">Sign in</Link>
              </Button>
              <Button asChild size="sm" className="font-semibold shadow-lg shadow-primary/25">
                <Link href="/signup">Get started</Link>
              </Button>
            </>
          )}
        </div>

        <div className="flex items-center gap-2 sm:hidden">
          {signedIn ? (
            <Button asChild size="sm" className="font-semibold shadow-lg shadow-primary/25">
              <Link href="/dashboard" onClick={() => setOpen(false)}>
                Dashboard
              </Link>
            </Button>
          ) : (
            <Button asChild size="sm" className="font-semibold">
              <Link href="/signup" onClick={() => setOpen(false)}>
                Start
              </Link>
            </Button>
          )}
          <button
            type="button"
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-zinc-600/80 text-zinc-200 md:hidden"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-label={open ? "Close menu" : "Open menu"}
          >
            {open ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>
      </div>

      <div
        className={cn(
          "border-t border-zinc-700/50 bg-zinc-950/95 md:hidden",
          open ? "block" : "hidden",
        )}
      >
        <nav
          className="flex max-h-[min(60dvh,calc(100dvh-4rem))] flex-col overflow-y-auto px-4 py-3"
          aria-label="Page sections"
        >
          {NAV.map((item) => (
            <a
              key={item.href}
              href={item.href}
              onClick={(e) => {
                setOpen(false);
                scrollToHash(e, item.href);
              }}
              className="rounded-lg px-3 py-2.5 text-sm font-medium text-zinc-100"
            >
              {item.label}
            </a>
          ))}
          <div className="mt-2 flex flex-col gap-0.5 border-t border-zinc-700/50 pt-3">
            {signedIn ? (
              <Link
                href="/dashboard"
                className="rounded-lg px-3 py-2.5 text-sm font-medium text-zinc-100"
                onClick={() => setOpen(false)}
              >
                Dashboard
              </Link>
            ) : (
              <>
                <Link
                  href="/login"
                  className="rounded-lg px-3 py-2.5 text-sm text-zinc-100"
                  onClick={() => setOpen(false)}
                >
                  Sign in
                </Link>
                <Link
                  href="/signup"
                  className="rounded-lg px-3 py-2.5 text-sm font-medium text-zinc-100"
                  onClick={() => setOpen(false)}
                >
                  Get started
                </Link>
              </>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
}
