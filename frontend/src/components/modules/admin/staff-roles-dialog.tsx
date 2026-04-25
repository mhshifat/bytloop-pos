"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Pencil } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Checkbox } from "@/components/shared/ui/checkbox";
import type { StaffMember } from "@/lib/api/auth";
import { updateStaffRoles } from "@/lib/api/auth";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { ALL_ROLES, roleDescription, roleLabel } from "@/lib/enums/role";

type StaffRolesDialogProps = {
  readonly member: StaffMember;
};

export function StaffRolesDialog({ member }: StaffRolesDialogProps) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [roles, setRoles] = useState<readonly string[]>(member.roles);
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const mutation = useMutation({
    mutationFn: () => updateStaffRoles(member.id, roles),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["staff"] });
      toast.success(`Updated roles for ${member.email}.`);
      setOpen(false);
    },
  });

  const toggleRole = (role: string): void => {
    setRoles((prev) =>
      prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role],
    );
  };

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (next) {
          setRoles(member.roles);
          setServerError(null);
        }
      }}
    >
      <Dialog.Trigger asChild>
        <Button variant="outline" size="icon-sm" aria-label={`Edit roles for ${member.email}`}>
          <Pencil size={14} />
        </Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface p-6 shadow-2xl focus:outline-none">
          <Dialog.Title className="text-lg font-semibold">Edit roles</Dialog.Title>
          <Dialog.Description className="mt-1 text-sm text-muted-foreground">
            {member.firstName} {member.lastName} · {member.email}
          </Dialog.Description>

          <div className="mt-4 space-y-2">
            {ALL_ROLES.map((role) => (
              <label
                key={role}
                className="flex items-start gap-2 rounded-md border border-border p-2 text-sm"
              >
                <Checkbox
                  checked={roles.includes(role)}
                  onCheckedChange={() => toggleRole(role)}
                  aria-label={roleLabel(role)}
                />
                <span className="flex-1">
                  <span className="block font-medium">{roleLabel(role)}</span>
                  <span className="block text-xs text-muted-foreground">
                    {roleDescription(role)}
                  </span>
                </span>
              </label>
            ))}
          </div>

          {serverError ? <InlineError error={serverError} /> : null}

          <div className="mt-4 flex justify-end gap-2">
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => mutation.mutate()}
              disabled={mutation.isPending || roles.length === 0}
            >
              {mutation.isPending ? "Saving…" : "Save roles"}
            </Button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
