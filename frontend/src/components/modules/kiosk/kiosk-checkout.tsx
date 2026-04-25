"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { CheckCircle2, CreditCard, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { checkout, type OrderRead } from "@/lib/api/sales";
import { useCartStore } from "@/lib/stores/cart-store";
import { formatMoney } from "@/lib/utils/money";

type Stage = "pay" | "success";

export function KioskCheckout() {
  const router = useRouter();
  const lines = useCartStore((s) => s.lines);
  const total = useCartStore((s) => s.totalCents());
  const clear = useCartStore((s) => s.clear);

  const [stage, setStage] = useState<Stage>("pay");
  const [order, setOrder] = useState<OrderRead | null>(null);
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const currency = lines[0]?.currency ?? "USD";

  const pay = useMutation({
    mutationFn: () =>
      checkout({
        items: lines.map((l) => ({
          productId: l.productId,
          quantity: l.quantity,
          verticalData: l.verticalData,
          exciseCents: l.exciseCents,
        })),
        paymentMethod: "card",
        amountTenderedCents: total,
      }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: (result) => {
      setServerError(null);
      setOrder(result);
      clear();
      setStage("success");
    },
  });

  // Auto-return to welcome 10s after a successful sale — next guest's turn.
  useEffect(() => {
    if (stage !== "success") return;
    const id = window.setTimeout(() => {
      router.push("/kiosk");
    }, 10_000);
    return () => window.clearTimeout(id);
  }, [stage, router]);

  if (stage === "success" && order) {
    return (
      <section className="flex min-h-screen flex-col items-center justify-center gap-6 p-6 text-center">
        <CheckCircle2 size={72} className="text-emerald-400" />
        <h1 className="text-4xl font-semibold tracking-tight">Thank you!</h1>
        <p className="text-lg text-muted-foreground">
          Order <span className="font-mono">#{order.number}</span>
        </p>
        <p className="text-base text-muted-foreground">
          Your receipt will print in a moment.
        </p>
        <Button
          size="lg"
          onClick={() => router.push("/kiosk")}
          className="h-14 px-10 text-base"
        >
          Done
        </Button>
      </section>
    );
  }

  return (
    <section className="flex min-h-screen flex-col items-center justify-center gap-6 p-6">
      <h1 className="text-3xl font-semibold tracking-tight">Ready to pay</h1>
      <p className="text-xl text-muted-foreground tabular-nums">
        Total {formatMoney(total, currency)}
      </p>
      <Button
        size="lg"
        onClick={() => pay.mutate()}
        disabled={pay.isPending || lines.length === 0}
        className="h-20 px-12 text-lg"
      >
        {pay.isPending ? (
          <>
            <Loader2 size={18} className="animate-spin" /> Processing…
          </>
        ) : (
          <>
            <CreditCard size={18} /> Tap card to pay
          </>
        )}
      </Button>
      {serverError ? (
        <div className="max-w-md">
          <InlineError error={serverError} />
        </div>
      ) : null}
      <Button
        variant="ghost"
        onClick={() => router.push("/kiosk/shop")}
        disabled={pay.isPending}
      >
        Back to menu
      </Button>
    </section>
  );
}
