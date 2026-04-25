import { BytloopLogoMark } from "@/components/shared/brand/bytloop-logo";
import {
  BarChart3,
  Coffee,
  Globe2,
  Layers3,
  Package,
  QrCode,
  Receipt,
  Shield,
  Store,
  Users,
  Wifi,
  Wrench,
} from "lucide-react";
import Link from "next/link";
import type { ComponentType } from "react";

import { Button } from "@/components/shared/ui/button";

import { SectionHeader } from "./marketing-section-header";

export function MarketingProductSection() {
  const bento: {
    title: string;
    text: string;
    icon: ComponentType<{ className?: string; "aria-hidden"?: boolean }>;
    className: string;
  }[] = [
    {
      icon: QrCode,
      title: "Lanes that keep moving",
      text: "Barcodes, quick keys, and tender flows tuned for high-traffic checkouts. Fewer errors at the handoff.",
      className: "sm:col-span-2",
    },
    {
      icon: Package,
      title: "Inventory that matches reality",
      text: "Variants, kits, and stock signals so back office and floor stay aligned.",
      className: "",
    },
    {
      icon: Receipt,
      title: "Receipts & tax",
      text: "Line-level clarity for discounts, voids, and tax lines — every basket explained.",
      className: "",
    },
    {
      icon: Users,
      title: "People & permissions",
      text: "Manager overrides, scoped roles, and a trail of who did what, when.",
      className: "sm:col-span-2",
    },
    {
      icon: BarChart3,
      title: "Live reporting",
      text: "Shift, tender, and product mix in one place — not five exported spreadsheets.",
      className: "",
    },
    {
      icon: Layers3,
      title: "Your business type, one product",
      text: "Switch retail, F&B, pharmacy, and more in settings; open KDS, batches, or custom orders from Verticals when you need depth—no parallel stack per format.",
      className: "",
    },
  ];

  return (
    <section
      id="product"
      className="scroll-mt-24 border-t border-zinc-800/80 bg-zinc-950/50 py-20 sm:py-28"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeader
          eyebrow="Product"
          title="Everything a serious operator expects—without the bloat"
          description="Lightning at the lane, stock you can stand behind, and numbers your team can act on. The same app runs the register, the catalog, and the guardrails—so you spend less time duct-taping spreadsheets."
        />
        <ul className="mt-16 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {bento.map((f) => (
            <li
              key={f.title}
              className={[
                "group relative overflow-hidden rounded-2xl border border-zinc-600/50 bg-zinc-900/70 p-6 shadow-xl shadow-black/20 ring-1 ring-white/5 transition hover:border-primary/40 hover:ring-primary/20",
                f.className,
              ]
                .filter(Boolean)
                .join(" ")}
            >
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl border border-zinc-600/50 bg-primary/15 text-primary">
                <f.icon className="size-6" aria-hidden />
              </div>
              <h3 className="text-lg font-semibold text-zinc-50">{f.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-zinc-300 sm:text-base">{f.text}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function MarketingIndustriesSection() {
  const items = [
    {
      icon: Store,
      title: "Retail & specialty",
      text: "Promotions, bundles, and per-store price books without maintaining parallel spreadsheets.",
    },
    {
      icon: Coffee,
      title: "Food & beverage",
      text: "Modifiers, holds, and kitchen / bar patterns that respect service speed and accuracy.",
    },
    {
      icon: Globe2,
      title: "Hospitality",
      text: "Stays, packages, and add-ons in flows guests and staff can follow in seconds.",
    },
    {
      icon: Wrench,
      title: "Services & trade",
      text: "Time-based and job-ticket flows for repairs, bookings, and on-site work.",
    },
  ] as const;

  return (
    <section
      id="industries"
      className="scroll-mt-24 border-t border-zinc-800/60 bg-linear-to-b from-violet-950/25 via-zinc-950/80 to-zinc-950/90 py-20 sm:py-28"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeader
          eyebrow="Sectors at a glance"
          title="Same engine. Different playbooks."
          description="You already saw concrete POS types above. Here is how we group them—one core platform that bends to retail floor, F&amp;B line, travel desk, or service bay without maintaining five different products under the hood."
        />
        <ul className="mt-16 grid gap-4 md:grid-cols-2">
          {items.map((f) => (
            <li
              key={f.title}
              className="relative flex gap-5 overflow-hidden rounded-2xl border border-zinc-600/40 bg-zinc-900/60 p-6 shadow-lg shadow-black/20 before:pointer-events-none before:absolute before:inset-0 before:bg-linear-to-br before:from-primary/10 before:to-transparent before:opacity-80"
            >
              <div className="relative z-10 flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-zinc-500/30 bg-zinc-950/80 text-primary">
                <f.icon className="size-7" aria-hidden />
              </div>
              <div className="relative z-10 min-w-0">
                <h3 className="text-lg font-semibold text-zinc-50">{f.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-zinc-300 sm:text-base">
                  {f.text}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function MarketingWorkflowSection() {
  const steps = [
    {
      n: "01",
      title: "Organize the business",
      text: "Create your org, add locations, and bring staff in with the right access from day one.",
    },
    {
      n: "02",
      title: "Model the real world",
      text: "Catalog, taxes, and lane profiles reflect how you run — not a demo dataset.",
    },
    {
      n: "03",
      title: "Open the lane",
      text: "Go live on shift with reporting that updates as the day unfolds.",
    },
  ] as const;

  return (
    <section
      id="workflow"
      className="scroll-mt-24 border-t border-zinc-800/80 bg-zinc-950/60 py-20 sm:py-28"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeader
          eyebrow="How it works"
          title="From first login to a live floor"
          description="Clear phases your team can communicate — from pilot store to org-wide rollouts."
        />
        <ol className="mt-16 grid gap-0 lg:grid-cols-3">
          {steps.map((s, i) => (
            <li
              key={s.n}
              className="relative border-b border-l-0 border-zinc-700/50 p-6 pb-10 lg:border-b-0 lg:border-l lg:px-8 lg:py-2 first:lg:pl-0 last:lg:pr-0"
            >
              {i > 0 ? (
                <span
                  className="absolute left-0 top-10 hidden h-px w-full -translate-y-1/2 bg-linear-to-r from-primary/0 via-primary/30 to-primary/0 lg:top-14 lg:block"
                  aria-hidden
                />
              ) : null}
              <div className="font-mono text-4xl font-bold text-primary">{s.n}</div>
              <h3 className="mt-3 text-xl font-semibold text-zinc-50">{s.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-zinc-300 sm:text-base">{s.text}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export function MarketingReliabilitySection() {
  const blocks = [
    {
      icon: Shield,
      title: "Zero-trust friendly",
      text: "Modern auth, TLS everywhere, and service boundaries that assume a hostile network.",
    },
    {
      icon: Wifi,
      title: "Offline-tolerant by design",
      text: "Lanes shouldn’t stop when a router hiccups — the architecture bakes in resilience for real retail.",
    },
    {
      icon: BarChart3,
      title: "Operable, observable",
      text: "Health, traces, and alerts in the platform layer — catch incidents before the lunch rush does.",
    },
  ] as const;

  return (
    <section
      id="reliability"
      className="scroll-mt-24 border-t border-zinc-800/80 bg-zinc-900/30 py-20 sm:py-28"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeader
          eyebrow="Platform"
          title="Serious about reliability & security"
          description="The same care we put into a crisp checkout experience goes into encryption, access control, and on-call–ready operations."
        />
        <ul className="mt-16 grid gap-4 md:grid-cols-3">
          {blocks.map((b) => (
            <li
              key={b.title}
              className="flex flex-col rounded-2xl border border-dashed border-primary/30 bg-zinc-950/80 p-6"
            >
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/20 text-primary">
                <b.icon className="size-6" aria-hidden />
              </div>
              <h3 className="text-lg font-semibold text-zinc-50">{b.title}</h3>
              <p className="mt-2 flex-1 text-sm leading-relaxed text-zinc-300 sm:text-base">
                {b.text}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function MarketingCtaSection() {
  return (
    <section
      id="get-started"
      className="scroll-mt-24 border-t border-zinc-800/60 bg-zinc-950/80 py-20 sm:py-28"
    >
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <div className="overflow-hidden rounded-3xl border border-zinc-600/50 bg-linear-to-br from-primary/25 via-zinc-900/90 to-fuchsia-950/40 p-1 shadow-2xl shadow-primary/20">
          <div className="rounded-[1.4rem] bg-zinc-950/90 px-6 py-12 sm:px-10 sm:py-14">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight text-zinc-50 sm:text-4xl">
                Ship your next rollout with a POS team members actually enjoy
              </h2>
              <p className="mt-4 text-pretty text-lg text-zinc-300">
                Open an account, invite a test lane, and explore the console. For multi-site programs,
                we’ll help you plan data migration, training, and go-live.
              </p>
              <div className="mt-8 flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center sm:gap-4">
                <Button
                  asChild
                  size="lg"
                  className="h-12 min-w-48 text-base font-semibold shadow-lg shadow-primary/30"
                >
                  <Link href="/signup">Create your workspace</Link>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="h-12 min-w-48 border-zinc-500 bg-zinc-900/50 text-zinc-100"
                >
                  <Link href="/login">I already have access</Link>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export function MarketingFooter() {
  return (
    <footer className="border-t border-zinc-800 bg-zinc-950 py-16">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-12 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <div className="flex items-center gap-2.5">
              <BytloopLogoMark className="h-9 w-9" />
              <p className="text-lg font-bold text-zinc-50">Bytloop POS</p>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-zinc-300">
              Cloud-native point-of-sale and back-office for teams that can’t afford downtime at the
              register.
            </p>
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-zinc-50">Product</p>
            <ul className="mt-4 space-y-2.5 text-sm text-zinc-300">
              <li>
                <a className="transition hover:text-white" href="#simplicity">
                  Why us
                </a>
              </li>
              <li>
                <a className="transition hover:text-white" href="#product">
                  Features
                </a>
              </li>
              <li>
                <a className="transition hover:text-white" href="#pos-types">
                  POS types
                </a>
              </li>
              <li>
                <a className="transition hover:text-white" href="#industries">
                  Sectors
                </a>
              </li>
              <li>
                <a className="transition hover:text-white" href="#workflow">
                  Workflow
                </a>
              </li>
              <li>
                <a className="transition hover:text-white" href="#reliability">
                  Platform
                </a>
              </li>
              <li>
                <a className="transition hover:text-white" href="#faq">
                  FAQ
                </a>
              </li>
            </ul>
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-zinc-50">Account</p>
            <ul className="mt-4 space-y-2.5 text-sm text-zinc-300">
              <li>
                <Link className="transition hover:text-white" href="/login">
                  Sign in
                </Link>
              </li>
              <li>
                <Link className="transition hover:text-white" href="/signup">
                  Create account
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-zinc-50">Contact</p>
            <p className="mt-4 text-sm leading-relaxed text-zinc-300">
              Partnerships, enterprise, and custom verticals:{" "}
              <a className="font-medium text-zinc-100 underline underline-offset-2" href="mailto:hello@bytloop.com">
                hello@bytloop.com
              </a>
            </p>
          </div>
        </div>
        <p className="mt-12 border-t border-zinc-800/80 pt-8 text-center text-sm text-zinc-500">
          © {new Date().getFullYear()} Bytloop. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
