"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plug, Power, Trash2 } from "lucide-react";
import { useMemo } from "react";
import { toast } from "sonner";

import { SkeletonCard } from "@/components/shared/skeleton-card";
import { Badge } from "@/components/shared/ui/badge";
import { Button } from "@/components/shared/ui/button";
import { Card } from "@/components/shared/ui/card";
import {
  installPlugin,
  listAvailablePlugins,
  listInstalledPlugins,
  togglePlugin,
  uninstallPlugin,
  type PluginInstall,
} from "@/lib/api/plugins";

export function PluginMarketplace() {
  const queryClient = useQueryClient();

  const { data: available, isLoading } = useQuery({
    queryKey: ["plugins", "available"],
    queryFn: () => listAvailablePlugins(),
  });
  const { data: installed } = useQuery({
    queryKey: ["plugins", "installed"],
    queryFn: () => listInstalledPlugins(),
  });

  const installedByCode = useMemo(() => {
    const map = new Map<string, PluginInstall>();
    for (const i of installed ?? []) {
      map.set(i.code, i);
    }
    return map;
  }, [installed]);

  const install = useMutation({
    mutationFn: (code: string) => installPlugin({ code, enabled: true }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["plugins", "installed"] });
      toast.success("Plugin installed.");
    },
  });

  const toggle = useMutation({
    mutationFn: (input: { code: string; enabled: boolean }) =>
      togglePlugin(input.code, input.enabled),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["plugins", "installed"] });
    },
  });

  const remove = useMutation({
    mutationFn: (code: string) => uninstallPlugin(code),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["plugins", "installed"] });
      toast.success("Plugin uninstalled.");
    },
  });

  if (isLoading) return <SkeletonCard />;

  return (
    <div className="grid gap-3 md:grid-cols-2">
      {(available ?? []).map((p) => {
        const i = installedByCode.get(p.code);
        const isInstalled = Boolean(i);
        const isEnabled = i?.enabled ?? false;
        return (
          <Card key={p.code} className="space-y-3 p-4">
            <header className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <Plug size={14} aria-hidden="true" />
                  <h3 className="text-base font-medium">{p.name}</h3>
                </div>
                <p className="text-xs text-muted-foreground">
                  v{p.version} · {p.code}
                </p>
              </div>
              {isInstalled ? (
                <Badge
                  variant="outline"
                  className={
                    isEnabled
                      ? "border-emerald-500/50 text-emerald-400"
                      : "border-amber-500/50 text-amber-400"
                  }
                >
                  {isEnabled ? "Enabled" : "Disabled"}
                </Badge>
              ) : null}
            </header>

            <p className="text-sm text-muted-foreground">{p.description}</p>

            <div className="flex flex-wrap gap-1">
              {p.hooks.map((h) => (
                <Badge key={h} variant="outline" className="font-mono text-xs">
                  {h}
                </Badge>
              ))}
            </div>

            <div className="flex items-center gap-2">
              {!isInstalled ? (
                <Button
                  size="sm"
                  onClick={() => install.mutate(p.code)}
                  disabled={install.isPending}
                >
                  Install
                </Button>
              ) : (
                <>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      toggle.mutate({ code: p.code, enabled: !isEnabled })
                    }
                    disabled={toggle.isPending}
                  >
                    <Power size={12} /> {isEnabled ? "Disable" : "Enable"}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      if (window.confirm(`Uninstall "${p.name}"?`)) {
                        remove.mutate(p.code);
                      }
                    }}
                    disabled={remove.isPending}
                  >
                    <Trash2 size={12} /> Uninstall
                  </Button>
                </>
              )}
            </div>
          </Card>
        );
      })}
    </div>
  );
}
