"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { getBrand, type TenantBrand, updateBrand } from "@/lib/api/tenant";

export function BrandSection() {
  const queryClient = useQueryClient();
  const { data } = useQuery({
    queryKey: ["tenant", "brand"],
    queryFn: () => getBrand(),
  });

  const [logoUrl, setLogoUrl] = useState("");
  const [primaryColor, setPrimaryColor] = useState("#6366f1");
  const [accentColor, setAccentColor] = useState("#a855f7");
  const [receiptHeader, setReceiptHeader] = useState("");
  const [receiptFooter, setReceiptFooter] = useState("");
  const [serverError, setServerError] = useState<ApiError | null>(null);

  // Seed from server once data arrives; further edits are local until save.
  useEffect(() => {
    if (!data) return;
    setLogoUrl(data.logoUrl ?? "");
    setPrimaryColor(data.primaryColor ?? "#6366f1");
    setAccentColor(data.accentColor ?? "#a855f7");
    setReceiptHeader(data.receiptHeader ?? "");
    setReceiptFooter(data.receiptFooter ?? "");
  }, [data]);

  const save = useMutation({
    mutationFn: (): Promise<TenantBrand> =>
      updateBrand({
        logoUrl: logoUrl || null,
        primaryColor: primaryColor || null,
        accentColor: accentColor || null,
        receiptHeader: receiptHeader || null,
        receiptFooter: receiptFooter || null,
      }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["tenant", "brand"] });
      toast.success("Brand updated.");
      setServerError(null);
    },
  });

  return (
    <div className="space-y-4 rounded-lg border border-border bg-surface p-4">
      <header>
        <h3 className="text-base font-medium">Brand</h3>
        <p className="text-sm text-muted-foreground">
          Logo, colors, receipt headers. Colors apply across the admin UI;
          receipt text prints on every sale.
        </p>
      </header>

      <div className="space-y-1.5">
        <Label htmlFor="brand-logo">Logo URL</Label>
        <Input
          id="brand-logo"
          value={logoUrl}
          onChange={(e) => setLogoUrl(e.target.value)}
          placeholder="https://cdn.example.com/logo.png"
        />
        {logoUrl ? (
          <div className="mt-2 flex items-center gap-2 rounded-md border border-border bg-background p-2">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={logoUrl} alt="Logo preview" className="h-10 w-auto" />
            <span className="text-xs text-muted-foreground">Preview</span>
          </div>
        ) : null}
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="brand-primary">Primary color</Label>
          <div className="flex items-center gap-2">
            <input
              type="color"
              value={primaryColor}
              onChange={(e) => setPrimaryColor(e.target.value)}
              className="h-9 w-12 cursor-pointer rounded border border-border bg-transparent"
              aria-label="Primary color picker"
            />
            <Input
              id="brand-primary"
              value={primaryColor}
              onChange={(e) => setPrimaryColor(e.target.value)}
              placeholder="#6366f1"
            />
          </div>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="brand-accent">Accent color</Label>
          <div className="flex items-center gap-2">
            <input
              type="color"
              value={accentColor}
              onChange={(e) => setAccentColor(e.target.value)}
              className="h-9 w-12 cursor-pointer rounded border border-border bg-transparent"
              aria-label="Accent color picker"
            />
            <Input
              id="brand-accent"
              value={accentColor}
              onChange={(e) => setAccentColor(e.target.value)}
              placeholder="#a855f7"
            />
          </div>
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="brand-header">Receipt header</Label>
        <Input
          id="brand-header"
          value={receiptHeader}
          onChange={(e) => setReceiptHeader(e.target.value)}
          placeholder="Thanks for shopping at Acme Co!"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="brand-footer">Receipt footer</Label>
        <Input
          id="brand-footer"
          value={receiptFooter}
          onChange={(e) => setReceiptFooter(e.target.value)}
          placeholder="Returns accepted within 30 days. www.example.com"
        />
      </div>

      {serverError ? <InlineError error={serverError} /> : null}

      <div className="flex justify-end">
        <Button onClick={() => save.mutate()} disabled={save.isPending}>
          {save.isPending ? "Saving…" : "Save brand"}
        </Button>
      </div>
    </div>
  );
}
