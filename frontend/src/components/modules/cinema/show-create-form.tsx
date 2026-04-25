"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { createShow } from "@/lib/api/cinema";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";

function parseSeatLabels(input: string): string[] {
  return Array.from(
    new Set(
      input
        .split(/[,\s]+/)
        .map((s) => s.trim().toUpperCase())
        .filter(Boolean),
    ),
  );
}

export function ShowCreateForm() {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const [screen, setScreen] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [endsAt, setEndsAt] = useState("");
  const [priceCents, setPriceCents] = useState(30000);
  const [mode, setMode] = useState<"grid" | "labels">("grid");
  const [rows, setRows] = useState(8);
  const [cols, setCols] = useState(12);
  const [seatsInput, setSeatsInput] = useState("A1, A2, A3, A4, A5, A6");
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const seatLabels = parseSeatLabels(seatsInput);
  const seatCount = mode === "grid" ? rows * cols : seatLabels.length;

  const mutation = useMutation({
    mutationFn: () =>
      createShow(
        mode === "grid"
          ? {
              title,
              screen,
              startsAt: new Date(startsAt).toISOString(),
              endsAt: new Date(endsAt).toISOString(),
              ticketPriceCents: priceCents,
              seatMapRows: rows,
              seatMapCols: cols,
            }
          : {
              title,
              screen,
              startsAt: new Date(startsAt).toISOString(),
              endsAt: new Date(endsAt).toISOString(),
              ticketPriceCents: priceCents,
              seatLabels,
            },
      ),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["cinema", "shows"] });
      setTitle("");
      setScreen("");
      setStartsAt("");
      setEndsAt("");
      setServerError(null);
      toast.success(`Show added with ${seatCount} seats.`);
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        mutation.mutate();
      }}
      className="grid gap-3 rounded-lg border border-border bg-surface p-4 md:grid-cols-6"
    >
      <div className="space-y-1.5 md:col-span-3">
        <Label htmlFor="show-title">Title</Label>
        <Input
          id="show-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5 md:col-span-2">
        <Label htmlFor="show-screen">Screen</Label>
        <Input
          id="show-screen"
          value={screen}
          onChange={(e) => setScreen(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="show-price">Price (cents)</Label>
        <Input
          id="show-price"
          type="number"
          min={0}
          value={priceCents}
          onChange={(e) => setPriceCents(Number(e.target.value))}
        />
      </div>
      <div className="space-y-1.5 md:col-span-2">
        <Label htmlFor="show-start">Starts</Label>
        <Input
          id="show-start"
          type="datetime-local"
          value={startsAt}
          onChange={(e) => setStartsAt(e.target.value)}
          required
        />
      </div>
      <div className="space-y-1.5 md:col-span-2">
        <Label htmlFor="show-end">Ends</Label>
        <Input
          id="show-end"
          type="datetime-local"
          value={endsAt}
          onChange={(e) => setEndsAt(e.target.value)}
          required
        />
      </div>
      <div className="md:col-span-6">
        <div className="mb-2 flex gap-4 text-sm">
          <label className="flex items-center gap-1.5">
            <input
              type="radio"
              checked={mode === "grid"}
              onChange={() => setMode("grid")}
            />
            Grid (rows × cols)
          </label>
          <label className="flex items-center gap-1.5">
            <input
              type="radio"
              checked={mode === "labels"}
              onChange={() => setMode("labels")}
            />
            Explicit labels
          </label>
        </div>
        {mode === "grid" ? (
          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="show-rows">Rows</Label>
              <Input
                id="show-rows"
                type="number"
                min={1}
                max={50}
                value={rows}
                onChange={(e) => setRows(Number(e.target.value))}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="show-cols">Seats per row</Label>
              <Input
                id="show-cols"
                type="number"
                min={1}
                max={50}
                value={cols}
                onChange={(e) => setCols(Number(e.target.value))}
              />
            </div>
          </div>
        ) : (
          <div className="space-y-1.5">
            <Label htmlFor="show-seats">Seats ({seatLabels.length})</Label>
            <Input
              id="show-seats"
              value={seatsInput}
              onChange={(e) => setSeatsInput(e.target.value)}
              placeholder="A1, A2, A3, B1, B2…"
            />
          </div>
        )}
        <p className="mt-1 text-xs text-muted-foreground">
          Will create {seatCount} seats.
        </p>
      </div>
      {serverError ? (
        <div className="md:col-span-6">
          <InlineError error={serverError} />
        </div>
      ) : null}
      <div className="md:col-span-6">
        <Button
          type="submit"
          disabled={mutation.isPending || !title || seatCount === 0}
        >
          Add show
        </Button>
      </div>
    </form>
  );
}
