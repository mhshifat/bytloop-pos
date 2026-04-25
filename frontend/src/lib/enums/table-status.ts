import type { TableStatus } from "@/lib/api/tables";

const LABELS: Record<TableStatus, string> = {
  available: "Available",
  occupied: "Occupied",
  reserved: "Reserved",
  cleaning: "Cleaning",
};

export function tableStatusLabel(status: TableStatus): string {
  return LABELS[status];
}

export const TABLE_STATUS_OPTIONS: readonly TableStatus[] = [
  "available",
  "occupied",
  "reserved",
  "cleaning",
];
