"use client";

import { Search, X } from "lucide-react";
import { useEffect, useState } from "react";

import { Input } from "@/components/shared/ui/input";

type SearchFilterProps = {
  readonly placeholder?: string;
  readonly value: string;
  readonly onChange: (value: string) => void;
  readonly debounceMs?: number;
  readonly onEnter?: () => void;
};

export function SearchFilter({
  placeholder = "Search…",
  value,
  onChange,
  debounceMs = 250,
  onEnter,
}: SearchFilterProps) {
  const [local, setLocal] = useState(value);

  useEffect(() => {
    setLocal(value);
  }, [value]);

  useEffect(() => {
    const t = setTimeout(() => {
      if (local !== value) onChange(local);
    }, debounceMs);
    return () => clearTimeout(t);
  }, [local, value, onChange, debounceMs]);

  return (
    <div className="relative">
      <Search
        size={14}
        aria-hidden="true"
        className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-muted)]"
      />
      <Input
        value={local}
        placeholder={placeholder}
        onChange={(e) => setLocal(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && onEnter) {
            e.preventDefault();
            // Flush debounce immediately so the parent sees the current value.
            if (local !== value) onChange(local);
            onEnter();
          }
        }}
        className="pl-8 pr-8"
      />
      {local ? (
        <button
          type="button"
          aria-label="Clear search"
          onClick={() => setLocal("")}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-[var(--color-muted)] hover:text-foreground"
        >
          <X size={12} />
        </button>
      ) : null}
    </div>
  );
}
