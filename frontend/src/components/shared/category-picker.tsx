"use client";

import { useQuery } from "@tanstack/react-query";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/shared/ui/select";
import { listCategories } from "@/lib/api/categories";

const NONE_VALUE = "__none__";

type CategoryPickerProps = {
  readonly value: string | null | undefined;
  readonly onChange: (value: string | null) => void;
  readonly id?: string;
};

export function CategoryPicker({ value, onChange, id }: CategoryPickerProps) {
  const { data } = useQuery({
    queryKey: ["categories"],
    queryFn: () => listCategories(),
  });

  return (
    <Select
      value={value ?? NONE_VALUE}
      onValueChange={(v) => onChange(v === NONE_VALUE ? null : v)}
    >
      <SelectTrigger id={id}>
        <SelectValue placeholder="Uncategorized" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={NONE_VALUE}>Uncategorized</SelectItem>
        {data?.map((c) => (
          <SelectItem key={c.id} value={c.id}>
            {c.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
