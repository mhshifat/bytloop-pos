"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/shared/ui/select";

type EnumSelectProps<T extends string> = {
  readonly value: T | undefined;
  readonly onChange: (value: T) => void;
  readonly options: readonly T[];
  readonly getLabel: (value: T) => string;
  readonly placeholder?: string;
  readonly disabled?: boolean;
  readonly id?: string;
  readonly "aria-label"?: string;
};

/**
 * Typed select that renders human labels for enum-like values.
 * See docs/PLAN.md §13 Enum display rule.
 */
export function EnumSelect<T extends string>({
  value,
  onChange,
  options,
  getLabel,
  placeholder = "Select…",
  disabled,
  id,
  "aria-label": ariaLabel,
}: EnumSelectProps<T>) {
  return (
    <Select value={value} onValueChange={(v) => onChange(v as T)} disabled={disabled}>
      <SelectTrigger id={id} aria-label={ariaLabel}>
        <SelectValue placeholder={placeholder}>
          {value ? getLabel(value) : undefined}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {options.map((opt) => (
          <SelectItem key={opt} value={opt}>
            {getLabel(opt)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
