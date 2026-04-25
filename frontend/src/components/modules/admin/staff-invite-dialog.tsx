"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { UserPlus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Checkbox } from "@/components/shared/ui/checkbox";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import { inviteStaff } from "@/lib/api/auth";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { ALL_ROLES, roleDescription, roleLabel } from "@/lib/enums/role";

export function StaffInviteDialog() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [roles, setRoles] = useState<string[]>(["cashier"]);
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const reset = (): void => {
    setFirstName("");
    setLastName("");
    setEmail("");
    setRoles(["cashier"]);
    setServerError(null);
  };

  const mutation = useMutation({
    mutationFn: () => inviteStaff({ firstName, lastName, email, roles }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["staff"] });
      toast.success(`Invitation sent to ${email}.`);
      setOpen(false);
      reset();
    },
  });

  const canSubmit =
    firstName.trim().length > 0 &&
    lastName.trim().length > 0 &&
    email.trim().length > 0 &&
    roles.length > 0;

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
        if (!next) reset();
      }}
    >
      <Dialog.Trigger asChild>
        <Button>
          <UserPlus size={14} /> Invite staff
        </Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface p-6 shadow-2xl focus:outline-none">
          <Dialog.Title className="text-lg font-semibold">Invite staff</Dialog.Title>
          <Dialog.Description className="mt-1 text-sm text-muted-foreground">
            They'll receive an activation email and pick their own password.
          </Dialog.Description>

          <form
            className="mt-4 space-y-3"
            onSubmit={(e) => {
              e.preventDefault();
              mutation.mutate();
            }}
          >
            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="invite-first">First name</Label>
                <Input
                  id="invite-first"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  autoFocus
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="invite-last">Last name</Label>
                <Input
                  id="invite-last"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="invite-email">Email</Label>
              <Input
                id="invite-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <fieldset className="space-y-2">
              <legend className="text-sm font-medium">Roles</legend>
              <div className="space-y-2">
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
            </fieldset>

            {serverError ? <InlineError error={serverError} /> : null}

            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={!canSubmit || mutation.isPending}>
                {mutation.isPending ? "Sending…" : "Send invitation"}
              </Button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
