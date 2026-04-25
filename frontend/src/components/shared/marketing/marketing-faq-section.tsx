"use client";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/shared/ui/accordion";

const ITEMS: { q: string; a: string }[] = [
  {
    q: "What is Bytloop POS?",
    a: "Bytloop POS is a modern point-of-sale and operations platform for retail, food & beverage, hospitality, and service businesses. Run the register, manage catalog and staff, and stay on top of reporting from one place.",
  },
  {
    q: "Can I use it in Bangladesh and internationally?",
    a: "Yes. The product is built with Bangladesh and global markets in mind—local compliance and multi-currency style workflows are part of the roadmap as we grow. Contact us for region-specific needs.",
  },
  {
    q: "Do you support offline selling?",
    a: "The stack includes an offline-minded architecture so lanes can keep working when connectivity is unstable; exact offline behaviour depends on your plan and device setup as we harden the experience.",
  },
  {
    q: "Is there a free trial or demo?",
    a: "You can create an account to explore the app. For multi-location rollouts, invoice billing, or custom verticals, reach out through the email in the footer.",
  },
  {
    q: "How is my data protected?",
    a: "We follow standard security practices: encryption in transit, least-privilege access for services, and ongoing hardening. Details scale with your deployment; enterprise customers can request documentation.",
  },
];

export function MarketingFaqSection() {
  return (
    <section
      id="faq"
      className="scroll-mt-24 border-t border-zinc-800/80 bg-zinc-950/40 py-20 sm:py-28"
    >
      <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
        <p className="text-center text-sm font-semibold uppercase tracking-[0.2em] text-primary">FAQ</p>
        <h2 className="mt-3 text-center text-3xl font-bold tracking-tight text-zinc-50 sm:text-4xl">
          Questions from teams evaluating a new POS
        </h2>
        <p className="mt-4 text-center text-base text-zinc-300 sm:text-lg">
          Short answers you can share with finance, IT, and store leadership.
        </p>
        <Accordion
          type="single"
          collapsible
          className="mt-12 w-full rounded-2xl border border-zinc-600/50 bg-zinc-900/50 px-2"
          defaultValue="item-0"
        >
          {ITEMS.map((item, i) => (
            <AccordionItem key={item.q} value={`item-${i}`} className="border-zinc-600/50 px-2 sm:px-3">
              <AccordionTrigger className="text-left text-base font-medium text-zinc-100 hover:no-underline sm:text-lg">
                {item.q}
              </AccordionTrigger>
              <AccordionContent className="pb-4 text-zinc-300 leading-relaxed">{item.a}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
}
