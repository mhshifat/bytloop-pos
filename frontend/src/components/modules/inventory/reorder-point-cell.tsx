"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, Pencil, X } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { setReorderPoint } from "@/lib/api/catalog";
import { isApiError } from "@/lib/api/error";

type ReorderPointCellProps = {
  readonly productId: string;
  readonly current: number;
};

export function ReorderPointCell({ productId, current }: ReorderPointCellProps) {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(String(current));

  const mutation = useMutation({
    mutationFn: () => setReorderPoint({ productId, reorderPoint: Number(value) }),
    onError: (err) => {
      if (isApiError(err)) toast.error(err.message);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["inventory", "levels"] });
      setEditing(false);
      toast.success("Reorder point updated.");
    },
  });

  if (!editing) {
    return (
      <div className="flex items-center justify-end gap-1.5">
        <span className="tabular-nums text-muted-foreground">{current || "—"}</span>
        <button
          type="button"
          aria-label="Edit reorder point"
          onClick={() => {
            setValue(String(current));
            setEditing(true);
          }}
          className="rounded p-1 text-muted-foreground hover:text-foreground"
        >
          <Pencil size={11} />
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-end gap-1">
      <Input
        type="number"
        min={0}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="h-7 w-20 text-right tabular-nums"
        autoFocus
      />
      <Button
        variant="ghost"
        size="icon-sm"
        aria-label="Save"
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending}
      >
        <Check size={12} />
      </Button>
      <Button
        variant="ghost"
        size="icon-sm"
        aria-label="Cancel"
        onClick={() => setEditing(false)}
      >
        <X size={12} />
      </Button>
    </div>
  );
}
