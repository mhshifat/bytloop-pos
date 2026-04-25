"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useRef, useState } from "react";

import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SearchFilter } from "@/components/shared/search-filter";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { isApiError } from "@/lib/api/error";
import { lookupVariant } from "@/lib/api/apparel";
import { lookupIsbn } from "@/lib/api/bookstore";
import { type Product, getProduct, listProducts } from "@/lib/api/catalog";
import { getProductDepartment } from "@/lib/api/departments";
import { getTenant } from "@/lib/api/tenant";
import { scanInput } from "@/lib/api/grocery";
import { useKeyboardShortcut } from "@/lib/hooks/use-keyboard-shortcut";
import { useCartStore } from "@/lib/stores/cart-store";
import { VerticalProfile, verticalProfileLabel } from "@/lib/enums/vertical-profile";
import { posStoreModeTagline } from "@/lib/verticals/pos-store-mode";
import { toast } from "sonner";

import { PosAssistantDialog } from "@/components/modules/ai/pos-assistant-dialog";

import { CartPanel } from "./cart-panel";
import { CheckoutFooter } from "./checkout-footer";
import { GroceryWeighDialog } from "./grocery-weigh-dialog";
import { ProductGrid } from "./product-grid";
import { ShiftIndicator } from "./shift-indicator";

function looksLikeIsbn(s: string): boolean {
  const t = s.replace(/[-\s]/g, "");
  return t.length === 10 || t.length === 13;
}

export function PosTerminal() {
  const [search, setSearch] = useState("");
  const [weighTarget, setWeighTarget] = useState<{
    readonly product: Product;
    readonly inputCode: string;
  } | null>(null);
  const addLine = useCartStore((s) => s.addLine);
  const clearCart = useCartStore((s) => s.clear);
  const checkoutButtonRef = useRef<HTMLButtonElement | null>(null);

  const { data: tenant } = useQuery({ queryKey: ["tenant"], queryFn: () => getTenant() });
  const profile = tenant?.verticalProfile ?? VerticalProfile.RETAIL_GENERAL;

  const { data, isLoading, error } = useQuery({
    queryKey: ["products", { search }],
    queryFn: () => listProducts({ search: search || undefined, pageSize: 40 }),
  });

  const addWithMeta = async (product: Product, extra?: { verticalData?: Record<string, unknown> }): Promise<void> => {
    const base = {
      productId: product.id,
      name: product.name,
      unitPriceCents: product.priceCents,
      currency: product.currency,
    };
    let verticalData = { ...extra?.verticalData };
    if (profile === VerticalProfile.RETAIL_DEPARTMENT) {
      try {
        const d = await getProductDepartment(product.id);
        verticalData = {
          ...verticalData,
          departmentId: d.departmentId,
          departmentName: d.departmentName,
          departmentCode: d.departmentCode,
        };
      } catch {
        // unassigned product — still allow sale
      }
    }
    if (Object.keys(verticalData).length > 0) {
      addLine({ ...base, verticalData });
    } else {
      addLine(base);
    }
  };

  const handleSelect = (product: Product): void => {
    void addWithMeta(product);
  };

  const tryResolveScan = async (raw: string): Promise<void> => {
    const term = raw.trim();
    if (!term) return;

    if (profile === VerticalProfile.RETAIL_GROCERY) {
      try {
        const s = await scanInput(term);
        if (s.productId) {
          const p = data?.items.find((x) => x.id === s.productId) ?? (await getProduct(s.productId));
          if (p && p.id === s.productId) {
            if (s.lineTotalCents != null) {
              addLine(
                {
                  productId: p.id,
                  name: p.name,
                  unitPriceCents: Math.round(s.lineTotalCents),
                  currency: p.currency,
                  verticalData: { groceryScan: true, inputCode: term },
                },
                1,
              );
            } else {
              setWeighTarget({ product: p, inputCode: term });
            }
            setSearch("");
            return;
          }
        }
      } catch {
        /* fall through */
      }
    }

    if (profile === VerticalProfile.RETAIL_BOOKSTORE && looksLikeIsbn(term)) {
      try {
        const b = await lookupIsbn(term);
        addLine({
          productId: b.id,
          name: b.name,
          unitPriceCents: b.priceCents,
          currency: b.currency,
          verticalData: { isbn: term },
        });
        setSearch("");
        return;
      } catch {
        toast.error("No book for that ISBN.");
        return;
      }
    }

    if (profile === VerticalProfile.RETAIL_APPAREL) {
      try {
        const v = await lookupVariant({ barcode: term, sku: term });
        const p = await getProduct(v.productId);
        if (p) {
          const price = v.priceCentsOverride ?? p.priceCents;
          addLine({
            productId: p.id,
            name: `${p.name} · ${v.size} / ${v.color}`,
            unitPriceCents: price,
            currency: p.currency,
            verticalData: {
              apparelVariantId: v.id,
              size: v.size,
              color: v.color,
            },
          });
          setSearch("");
          return;
        }
      } catch {
        /* fall through to grid */
      }
    }

    const items = data?.items ?? [];
    const t = term.toLowerCase();
    const match =
      items.find((p) => p.barcode?.toLowerCase() === t) ?? items.find((p) => p.sku.toLowerCase() === t);
    if (match) {
      void addWithMeta(match);
      setSearch("");
    }
  };

  const shortcuts = useMemo(
    () => [
      { key: "F8", handler: () => checkoutButtonRef.current?.click() },
      {
        key: "F9",
        handler: () => {
          if (window.confirm("Clear the current sale?")) clearCart();
        },
      },
      {
        key: "/",
        handler: () => {
          const el = document.querySelector<HTMLInputElement>(
            'input[placeholder*="Search products"]',
          );
          el?.focus();
        },
      },
      { key: "Escape", handler: () => setSearch(""), allowInInputs: true },
    ],
    [clearCart],
  );

  useKeyboardShortcut(shortcuts);

  return (
    <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-[1fr_380px] lg:items-stretch">
      <section className="flex min-h-0 flex-col gap-3">
        {profile !== VerticalProfile.RETAIL_GENERAL ? (
          <p className="rounded-md border border-border/80 bg-surface/60 px-3 py-2 text-xs text-muted-foreground">
            <span className="font-medium text-foreground">Store mode</span> {verticalProfileLabel(profile)}
            {" — "}
            {posStoreModeTagline(profile)}
          </p>
        ) : null}
        <SearchFilter
          value={search}
          onChange={setSearch}
          placeholder="Search products, scan barcode, ISBN, PLU…"
          onEnter={() => void tryResolveScan(search)}
        />
        {isLoading ? (
          <div className="grid auto-rows-fr grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <SkeletonCard key={i} lines={2} />
            ))}
          </div>
        ) : error && isApiError(error) ? (
          <InlineError error={error} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            title="No products yet"
            description="Add your first product to start taking orders."
          />
        ) : (
          <ProductGrid products={data.items} onSelect={handleSelect} />
        )}
      </section>

      <aside className="flex min-h-0 flex-col rounded-lg border border-border bg-surface">
        <header className="flex items-center justify-between gap-2 border-b border-border px-4 py-3">
          <h2 className="text-sm font-semibold">Current sale</h2>
          <div className="flex items-center gap-2">
            <PosAssistantDialog />
            <ShiftIndicator />
          </div>
        </header>
        <CartPanel verticalProfile={profile} />
        <CheckoutFooter checkoutButtonRef={checkoutButtonRef} />
      </aside>

      <div className="pointer-events-none fixed bottom-4 right-4 hidden rounded-md border border-border bg-surface px-3 py-1.5 text-xs text-muted-foreground shadow lg:block">
        <kbd className="font-mono">F8</kbd> charge · <kbd className="font-mono">F9</kbd> clear ·{" "}
        <kbd className="font-mono">/</kbd> search
      </div>

      {weighTarget ? (
        <GroceryWeighDialog
          open
          onOpenChange={(o) => {
            if (!o) setWeighTarget(null);
          }}
          product={weighTarget.product}
          inputCode={weighTarget.inputCode}
          tenantConfig={tenant?.config ?? null}
          onComplete={({ unitPriceCents, verticalData }) => {
            addLine({
              productId: weighTarget.product.id,
              name: weighTarget.product.name,
              unitPriceCents,
              currency: weighTarget.product.currency,
              verticalData: { ...verticalData, inputCode: weighTarget.inputCode },
            });
            setWeighTarget(null);
            setSearch("");
          }}
        />
      ) : null}
    </div>
  );
}
