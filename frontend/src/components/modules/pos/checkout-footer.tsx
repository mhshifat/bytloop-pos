"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { requiresVerification } from "@/lib/api/age-restricted";
import { getTenant } from "@/lib/api/tenant";
import { checkout, type AgeVerificationCheckout, type OrderRead } from "@/lib/api/sales";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { enqueue as enqueueOffline } from "@/lib/offline/queue";
import { useCartStore } from "@/lib/stores/cart-store";
import { usePosStore } from "@/lib/stores/pos-store";
import { formatMoney } from "@/lib/utils/money";
import { VerticalProfile } from "@/lib/enums/vertical-profile";

import { CustomerPicker } from "./customer-picker";
import { DiscountField } from "./discount-field";
import { ReceiptDialog } from "./receipt-dialog";
import { AgeVerificationDialog } from "./age-verification-dialog";

function isOffline(): boolean {
  return typeof navigator !== "undefined" && navigator.onLine === false;
}

type CheckoutFooterProps = {
  readonly checkoutButtonRef?: React.RefObject<HTMLButtonElement | null>;
};

export function CheckoutFooter({ checkoutButtonRef }: CheckoutFooterProps = {}) {
  const lines = useCartStore((s) => s.lines);
  const total = useCartStore((s) => s.totalCents());
  const clear = useCartStore((s) => s.clear);
  const customerId = usePosStore((s) => s.customerId);
  const discountCode = usePosStore((s) => s.discountCode);
  const resetPos = usePosStore((s) => s.reset);
  const queryClient = useQueryClient();
  const { data: tenant } = useQuery({ queryKey: ["tenant"], queryFn: () => getTenant() });

  const [serverError, setServerError] = useState<ApiError | null>(null);
  const [receipt, setReceipt] = useState<OrderRead | null>(null);
  const [ageOpen, setAgeOpen] = useState(false);
  const [ageMeta, setAgeMeta] = useState<{ pids: string[]; minAge: number } | null>(null);
  const [cannabisRef, setCannabisRef] = useState("");

  const profile = tenant?.verticalProfile ?? VerticalProfile.RETAIL_GENERAL;
  const currency = lines[0]?.currency ?? "BDT";

  const makePayload = (age?: AgeVerificationCheckout) => ({
    items: lines.map((l) => ({
      productId: l.productId,
      quantity: l.quantity,
      verticalData: l.verticalData,
      exciseCents: profile === VerticalProfile.RETAIL_LIQUOR ? l.exciseCents : undefined,
    })),
    orderType: "retail" as const,
    paymentMethod: "cash" as const,
    amountTenderedCents: total,
    customerId,
    discountCode,
    orderVerticalData: {
      verticalProfile: profile,
      ...(profile === VerticalProfile.RETAIL_CANNABIS && cannabisRef.trim()
        ? { complianceRef: cannabisRef.trim() }
        : {}),
    },
    ageVerification: age,
  });

  const doCheckout = async (age?: AgeVerificationCheckout): Promise<"online" | "queued"> => {
    if (isOffline()) {
      await enqueueOffline({ method: "POST", path: "/orders/checkout", body: makePayload(age) });
      return "queued";
    }
    const order = await checkout(makePayload(age));
    setReceipt(order);
    return "online";
  };

  const mutation = useMutation({
    mutationFn: (age?: AgeVerificationCheckout) => doCheckout(age),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async (result) => {
      clear();
      resetPos();
      setAgeMeta(null);
      setAgeOpen(false);
      await queryClient.invalidateQueries({ queryKey: ["products"] });
      if (result === "queued") {
        toast.success("Saved offline. Will sync when you're back online.");
      }
    },
  });

  const charge = async (): Promise<void> => {
    if (lines.length === 0) return;
    setServerError(null);
    const pids = [...new Set(lines.map((l) => l.productId))];
    const gated = await requiresVerification(pids);
    if (gated.length > 0) {
      setAgeMeta({
        pids: gated.map((g) => g.productId),
        minAge: Math.max(...gated.map((g) => g.minAgeYears)),
      });
      setAgeOpen(true);
      return;
    }
    mutation.mutate(undefined);
  };

  const disabled = lines.length === 0 || mutation.isPending;

  return (
    <>
      <AgeVerificationDialog
        open={ageOpen}
        onOpenChange={setAgeOpen}
        onConfirm={(isoDob) => {
          if (!ageMeta) return;
          mutation.mutate({ customerDob: isoDob, productIds: ageMeta.pids });
        }}
        minAgeHint={ageMeta?.minAge}
      />

      <div className="space-y-3 border-t border-border p-4">
        {profile === VerticalProfile.RETAIL_CANNABIS ? (
          <div className="space-y-1.5">
            <Label htmlFor="cannabis-ref" className="text-xs text-muted-foreground">
              Compliance note (METRC / internal ref)
            </Label>
            <Input
              id="cannabis-ref"
              value={cannabisRef}
              onChange={(e) => setCannabisRef(e.target.value)}
              placeholder="Optional — stored on order"
              className="h-9"
            />
          </div>
        ) : null}
        <CustomerPicker />
        <DiscountField />
        {serverError ? <InlineError error={serverError} /> : null}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Total (ex tax)</span>
          <span className="text-2xl font-semibold tabular-nums">
            {formatMoney(total, currency)}
          </span>
        </div>
        <p className="text-[11px] leading-snug text-muted-foreground">
          Final tax and totals are calculated on the server. Hardware tier and liquor
          excise are sent on this request.
        </p>
        <Button
          ref={checkoutButtonRef}
          size="lg"
          className="w-full"
          disabled={disabled}
          onClick={() => void charge()}
        >
          {mutation.isPending ? "Processing…" : isOffline() ? "Charge (offline)" : "Charge cash"}
        </Button>
      </div>
      <ReceiptDialog
        order={receipt}
        open={receipt !== null}
        onOpenChange={(open) => {
          if (!open) setReceipt(null);
        }}
      />
    </>
  );
}
