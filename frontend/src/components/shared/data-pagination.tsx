"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/shared/ui/button";

type DataPaginationProps = {
  readonly page: number;
  readonly pageSize: number;
  readonly hasMore: boolean;
  readonly total?: number;
  readonly onPageChange: (page: number) => void;
};

/**
 * Offset-safe pagination UI. Works with either total count or has-more
 * (cursor-style) backends — use `total` only when cheap to compute.
 */
export function DataPagination({
  page,
  pageSize,
  hasMore,
  total,
  onPageChange,
}: DataPaginationProps) {
  const start = (page - 1) * pageSize + 1;
  const end = total !== undefined ? Math.min(total, page * pageSize) : page * pageSize;

  return (
    <div className="flex items-center justify-between gap-3 text-sm text-[var(--color-muted)]">
      <p>
        {total !== undefined
          ? `Showing ${start}–${end} of ${total}`
          : `Page ${page}`}
      </p>
      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="icon-sm"
          aria-label="Previous page"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          <ChevronLeft size={14} />
        </Button>
        <Button
          variant="outline"
          size="icon-sm"
          aria-label="Next page"
          disabled={!hasMore}
          onClick={() => onPageChange(page + 1)}
        >
          <ChevronRight size={14} />
        </Button>
      </div>
    </div>
  );
}
