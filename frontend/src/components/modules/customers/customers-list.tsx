"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { DataPagination } from "@/components/shared/data-pagination";
import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SearchFilter } from "@/components/shared/search-filter";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { listCustomers } from "@/lib/api/customers";
import { isApiError } from "@/lib/api/error";

export function CustomersList() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading, error } = useQuery({
    queryKey: ["customers", { search, page }],
    queryFn: () => listCustomers({ search: search || undefined, page, pageSize: 25 }),
  });

  return (
    <div className="space-y-4">
      <div className="max-w-sm">
        <SearchFilter value={search} onChange={setSearch} placeholder="Search customers…" />
      </div>

      {isLoading ? (
        <div className="grid gap-2">
          <SkeletonCard /> <SkeletonCard /> <SkeletonCard />
        </div>
      ) : error && isApiError(error) ? (
        <InlineError error={error} />
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          title={search ? "No matches" : "No customers yet"}
          description={
            search ? "Try another search." : "Customers you add here will show up."
          }
        />
      ) : (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Phone</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((c) => (
                <TableRow
                  key={c.id}
                  className="cursor-pointer hover:bg-white/5"
                  onClick={() => {
                    window.location.href = `/customers/${c.id}`;
                  }}
                >
                  <TableCell>
                    {c.firstName} {c.lastName}
                  </TableCell>
                  <TableCell>{c.email ?? "—"}</TableCell>
                  <TableCell>{c.phone ?? "—"}</TableCell>
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
