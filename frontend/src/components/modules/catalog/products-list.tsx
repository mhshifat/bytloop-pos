"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { CategoryPicker } from "@/components/shared/category-picker";
import { DataPagination } from "@/components/shared/data-pagination";
import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SearchFilter } from "@/components/shared/search-filter";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Label } from "@/components/shared/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { listProducts } from "@/lib/api/catalog";
import { isApiError } from "@/lib/api/error";
import { formatMoney } from "@/lib/utils/money";

export function ProductsList() {
  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const pageSize = 25;

  const { data, isLoading, error } = useQuery({
    queryKey: ["products", { search, categoryId, page, pageSize }],
    queryFn: () =>
      listProducts({
        search: search || undefined,
        categoryId: categoryId ?? undefined,
        page,
        pageSize,
      }),
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <div className="min-w-64 flex-1">
          <Label className="sr-only" htmlFor="products-search">Search</Label>
          <SearchFilter value={search} onChange={setSearch} placeholder="Search products…" />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="products-category">Category</Label>
          <div className="w-52">
            <CategoryPicker
              id="products-category"
              value={categoryId}
              onChange={(v) => {
                setCategoryId(v);
                setPage(1);
              }}
            />
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-2">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      ) : error && isApiError(error) ? (
        <InlineError error={error} />
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          title={search ? "No products match" : "No products yet"}
          description={
            search
              ? "Try a different search term."
              : "Products you create will show up here."
          }
        />
      ) : (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>SKU</TableHead>
                <TableHead>Name</TableHead>
                <TableHead className="text-right">Price</TableHead>
                <TableHead className="text-right">Active</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((product) => (
                <TableRow
                  key={product.id}
                  className="cursor-pointer hover:bg-white/5"
                  onClick={() => {
                    window.location.href = `/products/${product.id}`;
                  }}
                >
                  <TableCell className="font-mono text-xs">{product.sku}</TableCell>
                  <TableCell>{product.name}</TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatMoney(product.priceCents, product.currency)}
                  </TableCell>
                  <TableCell className="text-right">
                    {product.isActive ? "Yes" : "No"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <DataPagination
            page={data.page}
            pageSize={data.pageSize}
            hasMore={data.hasMore}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
