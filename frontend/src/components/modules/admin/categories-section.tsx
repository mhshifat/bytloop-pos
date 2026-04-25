"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { EmptyState } from "@/components/shared/empty-state";
import { InlineError } from "@/components/shared/errors";
import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Button } from "@/components/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/shared/ui/card";
import { Input } from "@/components/shared/ui/input";
import { Label } from "@/components/shared/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/shared/ui/table";
import { createCategory, listCategories } from "@/lib/api/categories";
import type { ApiError } from "@/lib/api/error";
import { isApiError } from "@/lib/api/error";

function slugify(input: string): string {
  return input
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function CategoriesSection() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [serverError, setServerError] = useState<ApiError | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["categories"],
    queryFn: () => listCategories(),
  });

  const mutation = useMutation({
    mutationFn: () => createCategory({ slug: slug || slugify(name), name }),
    onError: (err) => {
      if (isApiError(err)) setServerError(err);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["categories"] });
      setName("");
      setSlug("");
      setServerError(null);
      toast.success("Category created.");
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Categories</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate();
          }}
          className="grid gap-3 md:grid-cols-3"
        >
          <div className="space-y-1.5">
            <Label htmlFor="cat-name">Name</Label>
            <Input
              id="cat-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cat-slug">Slug (optional)</Label>
            <Input
              id="cat-slug"
              value={slug}
              placeholder={name ? slugify(name) : "auto-from-name"}
              onChange={(e) => setSlug(e.target.value)}
            />
          </div>
          <div className="flex items-end">
            <Button type="submit" disabled={mutation.isPending || !name}>
              Add category
            </Button>
          </div>
        </form>

        {serverError ? <InlineError error={serverError} /> : null}

        {isLoading ? (
          <SkeletonCard />
        ) : error && isApiError(error) ? (
          <InlineError error={error} />
        ) : !data || data.length === 0 ? (
          <EmptyState title="No categories yet" description="Group your products." />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Slug</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((c) => (
                <TableRow key={c.id}>
                  <TableCell>{c.name}</TableCell>
                  <TableCell className="font-mono text-xs">{c.slug}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
