"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { LogIn } from "lucide-react";
import { toast } from "sonner";

import { ClassesList } from "@/components/modules/gym/classes-list";
import { PlansEditor } from "@/components/modules/gym/plans-editor";
import { EmptyState } from "@/components/shared/empty-state";
import { EnumBadge } from "@/components/shared/enum-display";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Button } from "@/components/shared/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { isApiError } from "@/lib/api/error";
import { checkIn, listMemberships, type MembershipStatus } from "@/lib/api/gym";

const STATUS_LABELS: Record<MembershipStatus, string> = {
  active: "Active",
  paused: "Paused",
  expired: "Expired",
  cancelled: "Cancelled",
};

export default function GymPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["gym", "memberships"],
    queryFn: () => listMemberships(),
  });

  const mutation = useMutation({
    mutationFn: (membershipId: string) => checkIn(membershipId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["gym"] });
      toast.success("Checked in.");
    },
    onError: (err) => {
      if (isApiError(err)) toast.error(err.message);
    },
  });

  return (
    <section className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Gym</h1>
        <p className="text-sm text-muted-foreground">
          Plans, memberships, check-ins, classes.
        </p>
      </header>

      <div className="space-y-2">
        <h2 className="text-lg font-medium">Plans</h2>
        <PlansEditor />
      </div>

      <div className="space-y-2">
        <h2 className="text-lg font-medium">Upcoming classes</h2>
        <ClassesList />
      </div>

      <div className="space-y-2">
        <h2 className="text-lg font-medium">Memberships</h2>
      {isLoading ? (
        <SkeletonCard />
      ) : error && isApiError(error) ? (
        <InlineError error={error} />
      ) : !data || data.length === 0 ? (
        <EmptyState title="No memberships yet" />
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Plan</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Starts</TableHead>
              <TableHead>Ends</TableHead>
              <TableHead className="text-right">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((m) => (
              <TableRow key={m.id}>
                <TableCell className="font-mono text-xs">{m.planCode}</TableCell>
                <TableCell>
                  <EnumBadge value={m.status} getLabel={(s) => STATUS_LABELS[s]} />
                </TableCell>
                <TableCell>{m.startsOn}</TableCell>
                <TableCell>{m.endsOn}</TableCell>
                <TableCell className="text-right">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={m.status !== "active" || mutation.isPending}
                    onClick={() => mutation.mutate(m.id)}
                  >
                    <LogIn size={12} /> Check in
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
      </div>
    </section>
  );
}
