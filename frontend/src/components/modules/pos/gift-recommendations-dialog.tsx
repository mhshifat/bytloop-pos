"use client";

import { useMutation } from "@tanstack/react-query";
import { Gift } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/shared/ui/dialog";
import { Textarea } from "@/components/shared/ui/textarea";
import { giftRecommendations } from "@/lib/api/gift-recommendations";
import { isApiError } from "@/lib/api/error";
import { getProduct } from "@/lib/api/catalog";
import { useCartStore } from "@/lib/stores/cart-store";

export function GiftRecommendationsDialog() {
  const addLine = useCartStore((s) => s.addLine);
  const [open, setOpen] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [budgetCents, setBudgetCents] = useState(5000);
  const [currency, setCurrency] = useState("BDT");

  const mut = useMutation({
    mutationFn: () => giftRecommendations({ prompt, budgetCents, currency }),
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button type="button" variant="outline" size="sm">
          <Gift size={14} aria-hidden="true" /> Gift help
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Gift recommendations</DialogTitle>
        </DialogHeader>

        <div className="grid gap-3 md:grid-cols-2">
          <div className="space-y-1.5 md:col-span-2">
            <Label htmlFor="gift-prompt">Prompt</Label>
            <Textarea
              id="gift-prompt"
              rows={4}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder='e.g. "Gift for my mom, loves gardening, elegant, not too flashy"'
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="gift-budget">Budget (cents)</Label>
            <Input id="gift-budget" type="number" min={0} value={budgetCents} onChange={(e) => setBudgetCents(Number(e.target.value))} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="gift-currency">Currency</Label>
            <Input id="gift-currency" maxLength={3} value={currency} onChange={(e) => setCurrency(e.target.value.toUpperCase())} />
          </div>
        </div>

        {mut.error && isApiError(mut.error) ? <InlineError error={mut.error} /> : null}

        {mut.data ? (
          <div className="space-y-2 rounded-md border border-border bg-background p-3 text-sm">
            {mut.data.products.map((p) => (
              <div key={p.productId} className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-medium">{p.productId.slice(0, 8)}…</p>
                  <p className="text-xs text-muted-foreground">{p.rationale}</p>
                </div>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onClick={async () => {
                    const prod = await getProduct(p.productId);
                    addLine({ productId: prod.id, name: prod.name, unitPriceCents: prod.priceCents, currency: prod.currency });
                    toast.success("Added to cart.");
                  }}
                >
                  Add
                </Button>
              </div>
            ))}
          </div>
        ) : null}

        <DialogFooter>
          <Button
            type="button"
            disabled={mut.isPending || prompt.trim().length === 0}
            onClick={() => mut.mutate()}
          >
            {mut.isPending ? "Thinking…" : "Recommend"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

