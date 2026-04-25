"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FilePlus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { Button } from "@/components/shared/ui/button";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/shared/ui/select";
import { listCustomers } from "@/lib/api/customers";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { createPrescription } from "@/lib/api/pharmacy";

export function PrescriptionForm() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [customerId, setCustomerId] = useState<string>("");
  const [prescriptionNo, setPrescriptionNo] = useState("");
  const [doctorName, setDoctorName] = useState("");
  const [doctorLicense, setDoctorLicense] = useState("");
  const [issuedOn, setIssuedOn] = useState(
    new Date().toISOString().slice(0, 10),
  );
  const [notes, setNotes] = useState("");
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const { data: customers } = useQuery({
    queryKey: ["customers", "for-rx"],
    queryFn: () => listCustomers({ pageSize: 100 }),
    enabled: open,
  });

  const reset = (): void => {
    setCustomerId("");
    setPrescriptionNo("");
    setDoctorName("");
    setDoctorLicense("");
    setIssuedOn(new Date().toISOString().slice(0, 10));
    setNotes("");
    setServerError(null);
  };

  const mutation = useMutation({
    mutationFn: () =>
      createPrescription({
        customerId: customerId || null,
        prescriptionNo,
        doctorName,
        doctorLicense: doctorLicense || null,
        issuedOn,
        notes: notes || null,
      }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["pharmacy", "prescriptions"] });
      toast.success("Prescription recorded.");
      setOpen(false);
      reset();
    },
  });

  const canSubmit =
    prescriptionNo.trim().length > 0 && doctorName.trim().length > 0;

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
          <FilePlus size={14} /> Record prescription
        </Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface p-6 shadow-2xl focus:outline-none">
          <Dialog.Title className="text-lg font-semibold">
            Record prescription
          </Dialog.Title>
          <Dialog.Description className="mt-1 text-sm text-muted-foreground">
            Required before dispensing any controlled substance.
          </Dialog.Description>

          <form
            className="mt-4 space-y-3"
            onSubmit={(e) => {
              e.preventDefault();
              mutation.mutate();
            }}
          >
            <div className="space-y-1.5">
              <Label htmlFor="rx-customer">Customer</Label>
              <Select value={customerId} onValueChange={setCustomerId}>
                <SelectTrigger id="rx-customer">
                  <SelectValue placeholder="Walk-in (no customer)" />
                </SelectTrigger>
                <SelectContent>
                  {customers?.items.map((c) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.firstName} {c.lastName}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="rx-no">Prescription #</Label>
                <Input
                  id="rx-no"
                  value={prescriptionNo}
                  onChange={(e) => setPrescriptionNo(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="rx-date">Issued on</Label>
                <Input
                  id="rx-date"
                  type="date"
                  value={issuedOn}
                  onChange={(e) => setIssuedOn(e.target.value)}
                  required
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="rx-doc">Doctor name</Label>
              <Input
                id="rx-doc"
                value={doctorName}
                onChange={(e) => setDoctorName(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="rx-lic">Doctor license (optional)</Label>
              <Input
                id="rx-lic"
                value={doctorLicense}
                onChange={(e) => setDoctorLicense(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="rx-notes">Notes</Label>
              <Input
                id="rx-notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>

            {serverError ? <InlineError error={serverError} /> : null}

            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={!canSubmit || mutation.isPending}>
                {mutation.isPending ? "Saving…" : "Save prescription"}
              </Button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
