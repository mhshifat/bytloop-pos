"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLayoutEffect, useState } from "react";
import { toast } from "sonner";

import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Button } from "@/components/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared/ui/card";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/shared/ui/select";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";
import { getTenant, updateTenant } from "@/lib/api/tenant";
import {
  VERTICAL_GROUPS,
  verticalProfileLabel,
  type VerticalProfile,
} from "@/lib/enums/vertical-profile";

const VALID_VERTICAL_PROFILES = new Set<VerticalProfile>(
  VERTICAL_GROUPS.flatMap((g) => g.options.map((o) => o.value)),
);

function verticalProfileFromTenant(
  t: { verticalProfile?: string; vertical_profile?: string } | null | undefined,
): VerticalProfile {
  const raw = (t?.verticalProfile ?? t?.vertical_profile ?? "retail_general") as string;
  const v = (typeof raw === "string" ? raw.trim() : "retail_general") as VerticalProfile;
  return VALID_VERTICAL_PROFILES.has(v) ? v : "retail_general";
}

export function TenantSection() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["tenant"],
    queryFn: () => getTenant(),
  });

  const [name, setName] = useState("");
  const [country, setCountry] = useState("");
  const [currency, setCurrency] = useState("");
  /** Local override; cleared whenever tenant query `data` updates so the Select tracks the server. */
  const [editProfile, setEditProfile] = useState<VerticalProfile | null>(null);
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const serverProfile = data ? verticalProfileFromTenant(data) : "retail_general";
  const profile: VerticalProfile = editProfile ?? serverProfile;

  useLayoutEffect(() => {
    if (!data) return;
    setName(data.name);
    setCountry(data.country);
    setCurrency(data.defaultCurrency);
    setEditProfile(null);
  }, [data]);

  const mutation = useMutation({
    mutationFn: () =>
      updateTenant({
        name,
        country: country.toUpperCase(),
        defaultCurrency: currency.toUpperCase(),
        verticalProfile: profile,
      }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["tenant"] });
      setServerError(null);
      toast.success("Workspace updated.");
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Workspace</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <SkeletonCard />
        ) : error && isApiError(error) ? (
          <InlineError error={error} />
        ) : !data ? null : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              setServerError(null);
              mutation.mutate();
            }}
            className="grid gap-3 md:grid-cols-4"
          >
            <div className="space-y-1.5 md:col-span-2">
              <Label htmlFor="tenant-name">Name</Label>
              <Input
                id="tenant-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="tenant-country">Country (ISO-2)</Label>
              <Input
                id="tenant-country"
                maxLength={2}
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="tenant-currency">Default currency</Label>
              <Input
                id="tenant-currency"
                maxLength={3}
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5 md:col-span-4">
              <Label htmlFor="tenant-profile">Business type</Label>
              <Select
                value={profile}
                onValueChange={(v) => setEditProfile(v as VerticalProfile)}
              >
                <SelectTrigger id="tenant-profile">
                  <SelectValue placeholder="Choose business type">
                    {profile ? verticalProfileLabel(profile) : undefined}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {VERTICAL_GROUPS.map((group) => (
                    <SelectGroup key={group.label}>
                      <SelectLabel>{group.label}</SelectLabel>
                      {group.options.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Shapes the POS UX. You can switch any time — data is preserved.
              </p>
            </div>
            <div className="md:col-span-4">
              <p className="mb-2 text-xs text-muted-foreground">
                Workspace slug: <span className="font-mono">{data.slug}</span>
              </p>
              {serverError ? <InlineError error={serverError} /> : null}
              <Button type="submit" disabled={mutation.isPending}>
                Save workspace
              </Button>
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  );
}
