"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";

import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Badge } from "@/components/shared/ui/badge";
import { Button } from "@/components/shared/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { listStaff, removeStaff } from "@/lib/api/auth";
import { isApiError } from "@/lib/api/error";
import { roleLabel } from "@/lib/enums/role";

import { StaffRolesDialog } from "./staff-roles-dialog";

type StaffListProps = {
  readonly currentUserId: string;
};

export function StaffList({ currentUserId }: StaffListProps) {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["staff"],
    queryFn: () => listStaff(),
  });

  const removal = useMutation({
    mutationFn: (id: string) => removeStaff(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["staff"] });
      toast.success("Staff member removed.");
    },
  });

  if (isLoading) return <SkeletonCard />;
  if (error && isApiError(error)) return <InlineError error={error} />;
  if (!data || data.length === 0) {
    return <EmptyState title="No staff yet" description="Invite your first teammate above." />;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Roles</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((member) => {
          const isSelf = member.id === currentUserId;
          return (
            <TableRow key={member.id}>
              <TableCell>
                {member.firstName} {member.lastName}
                {isSelf ? (
                  <span className="ml-2 text-xs text-muted-foreground">(you)</span>
                ) : null}
              </TableCell>
              <TableCell>{member.email}</TableCell>
              <TableCell>
                <div className="flex flex-wrap gap-1">
                  {member.roles.map((role) => (
                    <Badge key={role} variant="outline">
                      {roleLabel(role)}
                    </Badge>
                  ))}
                </div>
              </TableCell>
              <TableCell>
                {member.emailVerified ? (
                  <Badge variant="outline" className="border-emerald-500/50 text-emerald-400">
                    Active
                  </Badge>
                ) : (
                  <Badge variant="outline" className="border-amber-500/50 text-amber-400">
                    Pending
                  </Badge>
                )}
              </TableCell>
              <TableCell className="text-right">
                <div className="flex justify-end gap-1">
                  <StaffRolesDialog member={member} />
                  <Button
                    variant="outline"
                    size="icon-sm"
                    aria-label={`Remove ${member.email}`}
                    disabled={isSelf || removal.isPending}
                    onClick={() => {
                      if (window.confirm(`Remove ${member.email}? They'll lose access immediately.`)) {
                        removal.mutate(member.id);
                      }
                    }}
                  >
                    <Trash2 size={14} />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
