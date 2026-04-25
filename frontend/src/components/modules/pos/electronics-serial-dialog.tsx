"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { isApiError } from "@/lib/api/error";
import { listItems, type ElectronicsItem } from "@/lib/api/electronics";
import { useCartStore, type CartLine } from "@/lib/stores/cart-store";

type ElectronicsSerialDialogProps = {
  readonly open: boolean;
  readonly onOpenChange: (open: boolean) => void;
  readonly line: CartLine | null;
};

export function ElectronicsSerialDialog({ open, onOpenChange, line }: ElectronicsSerialDialogProps) {
  const updateLine = useCartStore((s) => s.updateLine);
  const [serial, setSerial] = useState("");
  const [imei, setImei] = useState("");

  const productId = line?.productId ?? "";
  const { data: units, error } = useQuery({
    queryKey: ["electronics", "items", productId],
    queryFn: () => listItems(productId),
    enabled: open && productId.length > 0,
  });

  const available = (units ?? []).filter((u) => u.soldOrderId == null);

  const apply = (item: ElectronicsItem, sn: string, im: string | null): void => {
    if (!line) return;
    updateLine(line.lineId, {
      verticalData: {
        ...line.verticalData,
        electronicsItemId: item.id,
        serialNo: sn,
        imei: im,
      },
    });
    onOpenChange(false);
    setSerial("");
    setImei("");
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 max-h-[90dvh] w-full max-w-md -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-lg border border-border bg-surface p-5 shadow-xl">
          <Dialog.Title className="text-lg font-semibold">Serial / IMEI</Dialog.Title>
          <Dialog.Description className="mt-1 text-sm text-muted-foreground">
            Link an inventory unit to this line. Required before payment for serialized
            electronics.
          </Dialog.Description>

          {line && error && isApiError(error) ? (
            <p className="mt-2 text-sm text-destructive">Could not load units.</p>
          ) : null}

          {available.length > 0 ? (
            <ul className="mt-4 max-h-48 space-y-1 overflow-y-auto text-sm">
              {available.map((u) => (
                <li key={u.id}>
                  <Button
                    type="button"
                    variant="outline"
                    className="h-auto w-full justify-start py-2 text-left font-mono text-xs"
                    onClick={() => apply(u, u.serialNo, u.imei)}
                  >
                    {u.serialNo}
                    {u.imei ? ` · IMEI ${u.imei}` : null}
                  </Button>
                </li>
              ))}
            </ul>
          ) : null}

          <div className="mt-4 space-y-3 border-t border-border pt-4">
            <div className="space-y-1.5">
              <Label htmlFor="es-serial">Serial number</Label>
              <Input
                id="es-serial"
                value={serial}
                onChange={(e) => setSerial(e.target.value)}
                placeholder="Scan or type serial"
                className="font-mono"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="es-imei">IMEI (optional)</Label>
              <Input
                id="es-imei"
                value={imei}
                onChange={(e) => setImei(e.target.value)}
                placeholder="15 digits"
                className="font-mono"
              />
            </div>
            <Button
              type="button"
              className="w-full"
              disabled={!line || !serial.trim()}
              onClick={() => {
                if (!line) return;
                updateLine(line.lineId, {
                  verticalData: {
                    ...line.verticalData,
                    serialNo: serial.trim(),
                    imei: imei.trim() || undefined,
                  },
                });
                onOpenChange(false);
                setSerial("");
                setImei("");
              }}
            >
              Use typed serial
            </Button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
