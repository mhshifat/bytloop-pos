"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { getAttributes, upsertAttributes } from "@/lib/api/jewelry";

type JewelryAttributesFormProps = {
  readonly productId: string;
};

export function JewelryAttributesForm({ productId }: JewelryAttributesFormProps) {
  const queryClient = useQueryClient();
  const [karat, setKarat] = useState(22);
  const [gross, setGross] = useState("0.000");
  const [net, setNet] = useState("0.000");
  const [cert, setCert] = useState("");
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["jewelry", productId],
    queryFn: () => getAttributes(productId),
    retry: false,
  });

  useEffect(() => {
    if (!data) return;
    setKarat(data.karat);
    setGross(data.grossGrams);
    setNet(data.netGrams);
    setCert(data.certificateNo ?? "");
  }, [data]);

  const mutation = useMutation({
    mutationFn: () => {
      const base = data
        ? {
            metal: data.metal,
            makingChargePct: data.makingChargePct,
            makingChargePerGramCents: data.makingChargePerGramCents,
            wastagePct: data.wastagePct,
            stoneValueCents: data.stoneValueCents,
          }
        : {
            metal: "gold",
            makingChargePct: "0",
            makingChargePerGramCents: 0,
            wastagePct: "0",
            stoneValueCents: 0,
          };
      return upsertAttributes(productId, {
        ...base,
        karat,
        grossGrams: gross,
        netGrams: net,
        certificateNo: cert || null,
      });
    },
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["jewelry", productId] });
      setServerError(null);
      toast.success("Jewelry attributes saved.");
    },
  });

  if (isLoading) return <SkeletonCard lines={2} />;

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate();
      }}
      className="grid gap-3 md:grid-cols-4"
    >
      <div className="space-y-1.5">
        <Label htmlFor="jewelry-karat">Karat</Label>
        <Input
          id="jewelry-karat"
          type="number"
          min={1}
          max={24}
          value={karat}
          onChange={(e) => setKarat(Number(e.target.value))}
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="jewelry-gross">Gross (g)</Label>
        <Input
          id="jewelry-gross"
          inputMode="decimal"
          value={gross}
          onChange={(e) => setGross(e.target.value)}
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="jewelry-net">Net (g)</Label>
        <Input
          id="jewelry-net"
          inputMode="decimal"
          value={net}
          onChange={(e) => setNet(e.target.value)}
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="jewelry-cert">Certificate no.</Label>
        <Input
          id="jewelry-cert"
          value={cert}
          onChange={(e) => setCert(e.target.value)}
        />
      </div>
      {serverError ? (
        <div className="md:col-span-4">
          <InlineError error={serverError} />
        </div>
      ) : null}
      <div className="md:col-span-4">
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Saving…" : data ? "Save attributes" : "Add attributes"}
        </Button>
      </div>
    </form>
  );
}
