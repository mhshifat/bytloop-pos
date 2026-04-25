"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useState } from "react";

import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { weigh } from "@/lib/api/grocery";
import { useSerialScale } from "@/lib/hooks/use-serial-scale";
import { isWebSerialScaleEnabled } from "@/lib/pos/web-serial-flags";
import type { Product } from "@/lib/api/catalog";

type GroceryWeighDialogProps = {
  readonly open: boolean;
  readonly onOpenChange: (open: boolean) => void;
  readonly product: Product;
  readonly inputCode: string;
  /** Tenant config to enable Web Serial in addition to env. */
  readonly tenantConfig: Record<string, unknown> | null;
  /** Called with resolved line price from API after weigh. */
  onComplete: (payload: {
    unitPriceCents: number;
    grams: number;
    verticalData: Record<string, unknown>;
  }) => void;
};

export function GroceryWeighDialog({
  open,
  onOpenChange,
  product,
  inputCode,
  tenantConfig,
  onComplete,
}: GroceryWeighDialogProps) {
  const [manual, setManual] = useState("500");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const showSerial = isWebSerialScaleEnabled(tenantConfig);
  const scale = useSerialScale(9600);

  const applyGrams = async (grams: number): Promise<void> => {
    const g = Math.max(1, Math.round(grams));
    setErr(null);
    setBusy(true);
    try {
      const w = await weigh({ productId: product.id, grams: g });
      onComplete({
        unitPriceCents: w.priceCents,
        grams: g,
        verticalData: { weightGrams: g, inputCode, webSerial: scale.status === "open" },
      });
      onOpenChange(false);
      setManual("500");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Weigh failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface p-5 shadow-xl">
          <Dialog.Title className="text-lg font-semibold">Weigh: {product.name}</Dialog.Title>
          <Dialog.Description className="mt-1 text-sm text-muted-foreground">
            Enter weight in <strong>grams</strong> for the scanned item. This calls{" "}
            <code className="text-xs">/grocery/weigh</code>.
          </Dialog.Description>
          {showSerial ? (
            <div className="mt-4 space-y-2 rounded-md border border-dashed border-border/80 p-3 text-xs text-muted-foreground">
              <p className="font-medium text-foreground">USB scale (Chrome / Edge)</p>
              {!scale.isSupported ? (
                <p>Web Serial is not supported in this browser. Use manual grams.</p>
              ) : (
                <>
                  <div className="flex flex-wrap gap-2">
                    {scale.status === "open" ? (
                      <Button type="button" size="sm" variant="outline" onClick={() => void scale.disconnect()}>
                        Disconnect
                      </Button>
                    ) : (
                      <Button
                        type="button"
                        size="sm"
                        onClick={() => void scale.connect()}
                        disabled={scale.status === "connecting"}
                      >
                        {scale.status === "connecting" ? "Connecting…" : "Connect USB scale…"}
                      </Button>
                    )}
                    {scale.lastGrams != null && scale.status === "open" ? (
                      <Button
                        type="button"
                        size="sm"
                        onClick={() => void applyGrams(scale.lastGrams as number)}
                        disabled={busy}
                      >
                        Use {scale.lastGrams} g
                      </Button>
                    ) : null}
                  </div>
                  {scale.error ? <p className="text-destructive">{scale.error}</p> : null}
                  {scale.lastLine ? (
                    <p className="font-mono text-[10px] text-muted-foreground/90">
                      {scale.lastLine}
                    </p>
                  ) : null}
                </>
              )}
            </div>
          ) : null}
          <div className="mt-4 space-y-2">
            <Label htmlFor="g-grams">Grams (manual)</Label>
            <Input
              id="g-grams"
              type="number"
              min={1}
              value={manual}
              onChange={(e) => setManual(e.target.value)}
            />
            {err ? <p className="text-sm text-destructive">{err}</p> : null}
          </div>
          <div className="mt-5 flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={busy}>
              Cancel
            </Button>
            <Button
              type="button"
              onClick={() => void applyGrams(Number(manual) || 0)}
              disabled={busy}
            >
              {busy ? "Weighing…" : "Add to sale"}
            </Button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
