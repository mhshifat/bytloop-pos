"use client";

import { useQuery } from "@tanstack/react-query";
import { UserPlus, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { listCustomers } from "@/lib/api/customers";
import { usePosStore } from "@/lib/stores/pos-store";

export function CustomerPicker() {
  const customerId = usePosStore((s) => s.customerId);
  const customerLabel = usePosStore((s) => s.customerLabel);
  const setCustomer = usePosStore((s) => s.setCustomer);

  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  const { data } = useQuery({
    queryKey: ["customers", "pos", { search }],
    queryFn: () => listCustomers({ search: search || undefined, pageSize: 10 }),
    enabled: open,
  });

  if (customerId && customerLabel) {
    return (
      <div className="flex items-center justify-between gap-2 rounded-md bg-white/5 px-3 py-2 text-sm">
        <span>
          <span className="text-muted-foreground">Customer:</span> {customerLabel}
        </span>
        <button
          type="button"
          onClick={() => setCustomer(null, null)}
          aria-label="Remove customer"
          className="text-muted-foreground hover:text-foreground"
        >
          <X size={14} />
        </button>
      </div>
    );
  }

  if (!open) {
    return (
      <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
        <UserPlus size={14} /> Attach customer
      </Button>
    );
  }

  return (
    <div className="space-y-2 rounded-md border border-border p-2">
      <Input
        autoFocus
        placeholder="Search by name, email, or phone…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <div className="max-h-48 overflow-y-auto">
        {data?.items.map((c) => {
          const label = `${c.firstName} ${c.lastName}`.trim();
          return (
            <button
              key={c.id}
              type="button"
              onClick={() => {
                setCustomer(c.id, label);
                setOpen(false);
              }}
              className="w-full rounded px-2 py-1.5 text-left text-sm hover:bg-white/5"
            >
              <span>{label}</span>
              <span className="ml-2 text-xs text-muted-foreground">
                {c.email ?? c.phone ?? ""}
              </span>
            </button>
          );
        })}
        {data && data.items.length === 0 ? (
          <p className="p-2 text-xs text-muted-foreground">No matches.</p>
        ) : null}
      </div>
      <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>
        Cancel
      </Button>
    </div>
  );
}
