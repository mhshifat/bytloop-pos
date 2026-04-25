"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { CopyIdButton } from "@/components/shared/errors";
import { DataPagination } from "@/components/shared/data-pagination";
import { EmptyState } from "@/components/shared/empty-state";
import { EntityLabel } from "@/components/shared/entity-label";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { listAudit } from "@/lib/api/audit";
import { isApiError } from "@/lib/api/error";
import { auditActionLabel, resourceTypeLabel } from "@/lib/enums/audit-action";

const RESOURCE_HREF: Record<string, (id: string) => string> = {
  customer: (id) => `/customers/${id}`,
  product: (id) => `/products/${id}`,
  order: (id) => `/orders/${id}`,
  purchase_order: (id) => `/purchase-orders/${id}`,
};

export function AuditLogList() {
  const [page, setPage] = useState(1);

  const { data, isLoading, error } = useQuery({
    queryKey: ["audit", { page }],
    queryFn: () => listAudit({ page, pageSize: 50 }),
  });

  if (isLoading) return <SkeletonCard />;
  if (error && isApiError(error)) return <InlineError error={error} />;
  if (!data || data.items.length === 0) {
    return <EmptyState title="No audit events yet" description="Events appear here as they happen." />;
  }

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>When</TableHead>
            <TableHead>Actor</TableHead>
            <TableHead>Action</TableHead>
            <TableHead>Resource</TableHead>
            <TableHead>Correlation</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.items.map((e) => {
            const toHref = RESOURCE_HREF[e.resourceType];
            const href = e.resourceId && toHref != null ? toHref(e.resourceId) : null;
            return (
              <TableRow key={e.id}>
                <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                  {new Date(e.createdAt).toLocaleString()}
                </TableCell>
                <TableCell className="text-sm">
                  <EntityLabel id={e.actorId} entity="user" fallback="System" />
                </TableCell>
                <TableCell className="text-sm">{auditActionLabel(e.action)}</TableCell>
                <TableCell className="text-sm">
                  {href ? (
                    <a href={href} className="hover:underline">
                      {resourceTypeLabel(e.resourceType)}
                    </a>
                  ) : (
                    <span>{resourceTypeLabel(e.resourceType)}</span>
                  )}
                </TableCell>
                <TableCell>
                  {e.correlationId ? (
                    <CopyIdButton correlationId={e.correlationId} />
                  ) : (
                    "—"
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
      <DataPagination
        page={data.page}
        pageSize={data.pageSize}
        hasMore={data.hasMore}
        onPageChange={setPage}
      />
    </div>
  );
}
