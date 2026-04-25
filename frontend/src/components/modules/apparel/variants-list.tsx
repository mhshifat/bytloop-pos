"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { Minus, Plus } from "lucide-react";
import { toast } from "sonner";

import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import {
  adjustVariantStock,
  listVariants,
  updateVariant,
} from "@/lib/api/apparel";
import { isApiError } from "@/lib/api/error";

type VariantsListProps = {
  readonly productId: string;
};

export function VariantsList({ productId }: VariantsListProps) {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["apparel", "variants", productId],
    queryFn: () => listVariants(productId),
  });

  const patch = useMutation({
    mutationFn: (input: {
      id: string;
      barcode?: string | null;
      gender?: string | null;
      fit?: string | null;
      material?: string | null;
    }) => updateVariant(input.id, input),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["apparel", "variants", productId],
      });
    },
  });

  const adjust = useMutation({
    mutationFn: (input: { id: string; delta: number }) =>
      adjustVariantStock(input.id, input.delta),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["apparel", "variants", productId],
      });
      toast.success("Stock updated.");
    },
  });

  if (isLoading) return <SkeletonCard />;
  if (error && isApiError(error)) return <InlineError error={error} />;

  if (!data || data.length === 0) {
    return (
      <EmptyState
        title="No apparel variants"
        description="Use the matrix generator to create size × color SKUs."
        action={
          <Button asChild size="sm">
            <Link href={`/verticals/apparel/${productId}`}>Generate matrix</Link>
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-2">
      <h3 className="text-base font-medium">Variants</h3>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>SKU</TableHead>
            <TableHead>Size</TableHead>
            <TableHead>Color</TableHead>
            <TableHead className="w-36">Barcode</TableHead>
            <TableHead className="w-24">Gender</TableHead>
            <TableHead className="w-28">Fit</TableHead>
            <TableHead className="w-32">Material</TableHead>
            <TableHead className="w-32 text-right">Stock</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((v) => (
            <TableRow key={v.id}>
              <TableCell className="font-mono text-xs">{v.sku}</TableCell>
              <TableCell>{v.size}</TableCell>
              <TableCell>{v.color}</TableCell>
              <TableCell>
                <Input
                  defaultValue={v.barcode ?? ""}
                  placeholder="scan…"
                  onBlur={(e) => {
                    const next = e.target.value.trim() || null;
                    if (next !== (v.barcode ?? null)) {
                      patch.mutate({ id: v.id, barcode: next });
                    }
                  }}
                />
              </TableCell>
              <TableCell>
                <Input
                  defaultValue={v.gender ?? ""}
                  placeholder="M / F / U"
                  maxLength={8}
                  onBlur={(e) => {
                    const next = e.target.value.trim() || null;
                    if (next !== (v.gender ?? null)) {
                      patch.mutate({ id: v.id, gender: next });
                    }
                  }}
                />
              </TableCell>
              <TableCell>
                <Input
                  defaultValue={v.fit ?? ""}
                  placeholder="slim"
                  onBlur={(e) => {
                    const next = e.target.value.trim() || null;
                    if (next !== (v.fit ?? null)) {
                      patch.mutate({ id: v.id, fit: next });
                    }
                  }}
                />
              </TableCell>
              <TableCell>
                <Input
                  defaultValue={v.material ?? ""}
                  placeholder="cotton"
                  onBlur={(e) => {
                    const next = e.target.value.trim() || null;
                    if (next !== (v.material ?? null)) {
                      patch.mutate({ id: v.id, material: next });
                    }
                  }}
                />
              </TableCell>
              <TableCell>
                <div className="flex items-center justify-end gap-1">
                  <Button
                    size="icon-sm"
                    variant="outline"
                    aria-label="Decrement"
                    disabled={v.stockQuantity <= 0}
                    onClick={() => adjust.mutate({ id: v.id, delta: -1 })}
                  >
                    <Minus size={12} />
                  </Button>
                  <span className="w-10 text-right tabular-nums">{v.stockQuantity}</span>
                  <Button
                    size="icon-sm"
                    variant="outline"
                    aria-label="Increment"
                    onClick={() => adjust.mutate({ id: v.id, delta: 1 })}
                  >
                    <Plus size={12} />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
