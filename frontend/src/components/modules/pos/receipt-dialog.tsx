"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { Printer } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/shared/ui/button";
import { printReceipt, type Receipt } from "@/lib/print/escpos";
import type { OrderRead } from "@/lib/api/sales";
import { formatMoney } from "@/lib/utils/money";

type ReceiptDialogProps = {
  readonly order: OrderRead | null;
  readonly open: boolean;
  readonly onOpenChange: (open: boolean) => void;
};

function buildReceipt(order: OrderRead): Receipt {
  const money = (cents: number): string => formatMoney(cents, order.currency);
  const lines = order.items.map((i) => {
    const v = i.verticalData ?? {};
    const note = [v.serialNo && `S/N ${v.serialNo}`, v.departmentName && String(v.departmentName)]
      .filter(Boolean)
      .join(" · ");
    return {
      left: `${i.quantity} × ${i.nameSnapshot}${note ? `\n  ${note}` : ""}`,
      right: money(i.lineTotalCents),
    };
  });
  const totals: { left: string; right?: string }[] = [
    { left: "Subtotal", right: money(order.subtotalCents) },
    { left: "Tax", right: money(order.taxCents) },
  ];
  if (order.discountCents > 0) {
    totals.push({ left: "Discount", right: `-${money(order.discountCents)}` });
  }
  totals.push({ left: "Total", right: money(order.totalCents) });
  if (order.changeDueCents > 0) {
    totals.push({ left: "Change due", right: money(order.changeDueCents) });
  }
  return {
    header: ["Bytloop POS", `Receipt #${order.number}`],
    lines,
    totals,
    footer: ["Thank you!"],
  };
}

async function handlePrint(order: OrderRead): Promise<void> {
  try {
    await printReceipt(buildReceipt(order));
  } catch (err) {
    console.error(err);
    toast.error("Couldn't reach the printer. Falling back to browser print.");
    window.print();
  }
}

export function ReceiptDialog({ order, open, onOpenChange }: ReceiptDialogProps) {
  return (
    <Dialog.Root open={open && order !== null} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface p-6 shadow-2xl focus:outline-none">
          {order ? (
            <>
              <Dialog.Title className="text-lg font-semibold">Receipt #{order.number}</Dialog.Title>
              <Dialog.Description className="mt-1 text-xs text-muted-foreground">
                Completed · {order.currency}
              </Dialog.Description>

              <ul className="mt-4 divide-y divide-border text-sm">
                {order.items.map((item) => (
                  <li key={item.id} className="flex justify-between py-2">
                    <div>
                      <p>{item.nameSnapshot}</p>
                      <p className="text-xs text-muted-foreground">
                        {item.quantity} × {formatMoney(item.unitPriceCents, order.currency)}
                      </p>
                    </div>
                    <span className="tabular-nums">
                      {formatMoney(item.lineTotalCents, order.currency)}
                    </span>
                  </li>
                ))}
              </ul>

              <div className="mt-4 space-y-1.5 border-t border-border pt-4 text-sm">
                <Row label="Subtotal" value={formatMoney(order.subtotalCents, order.currency)} />
                <Row label="Tax" value={formatMoney(order.taxCents, order.currency)} />
                <Row
                  label="Total"
                  value={formatMoney(order.totalCents, order.currency)}
                  bold
                />
                {order.changeDueCents > 0 ? (
                  <Row
                    label="Change due"
                    value={formatMoney(order.changeDueCents, order.currency)}
                  />
                ) : null}
              </div>

              <div className="mt-6 flex justify-end gap-2">
                <Button variant="outline" onClick={() => handlePrint(order)}>
                  <Printer size={14} /> Print
                </Button>
                <Button onClick={() => onOpenChange(false)}>Done</Button>
              </div>
            </>
          ) : null}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function Row({ label, value, bold = false }: { readonly label: string; readonly value: string; readonly bold?: boolean }) {
  return (
    <div className="flex justify-between">
      <span className={bold ? "font-semibold" : "text-muted-foreground"}>{label}</span>
      <span className={bold ? "font-semibold tabular-nums" : "tabular-nums"}>{value}</span>
    </div>
  );
}
