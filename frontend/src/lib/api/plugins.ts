import { apiFetch } from "./fetcher";

export type PluginMeta = {
  readonly code: string;
  readonly name: string;
  readonly description: string;
  readonly version: string;
  readonly hooks: readonly string[];
};

export type PluginInstall = {
  readonly id: string;
  readonly code: string;
  readonly enabled: boolean;
  readonly config: Record<string, unknown>;
  readonly installedAt: string;
};

export async function listAvailablePlugins(): Promise<readonly PluginMeta[]> {
  return apiFetch<readonly PluginMeta[]>("/plugins/available");
}

export async function listInstalledPlugins(): Promise<readonly PluginInstall[]> {
  return apiFetch<readonly PluginInstall[]>("/plugins/installed");
}

export async function installPlugin(input: {
  readonly code: string;
  readonly enabled?: boolean;
  readonly config?: Record<string, unknown>;
}): Promise<PluginInstall> {
  return apiFetch<PluginInstall>("/plugins/install", {
    method: "POST",
    json: input,
  });
}

export async function togglePlugin(
  code: string,
  enabled: boolean,
): Promise<PluginInstall> {
  return apiFetch<PluginInstall>(`/plugins/${code}`, {
    method: "PATCH",
    json: { enabled },
  });
}

export async function uninstallPlugin(code: string): Promise<void> {
  return apiFetch<void>(`/plugins/${code}`, { method: "DELETE" });
}
