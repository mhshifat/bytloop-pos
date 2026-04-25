import type { SeatStatus } from "@/lib/api/cinema";

const LABELS: Record<SeatStatus, string> = {
  available: "Available",
  held: "Held",
  sold: "Sold",
};

export function seatStatusLabel(status: SeatStatus): string {
  return LABELS[status];
}
