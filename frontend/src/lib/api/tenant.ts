import { apiFetch } from "./fetcher";

export type Tenant = {
  readonly id: string;
  readonly slug: string;
  readonly name: string;
  readonly country: string;
  readonly defaultCurrency: string;
  readonly verticalProfile: string;
  readonly config: Record<string, unknown>;
};

export async function getTenant(): Promise<Tenant> {
  return apiFetch<Tenant>("/tenant");
}

export type TenantUpdateInput = {
  readonly name?: string;
  readonly country?: string;
  readonly defaultCurrency?: string;
  readonly verticalProfile?: string;
};

export async function updateTenant(input: TenantUpdateInput): Promise<Tenant> {
  return apiFetch<Tenant>("/tenant", { method: "PATCH", json: input });
}

export type TenantBrand = {
  readonly logoUrl: string | null;
  readonly primaryColor: string | null;
  readonly accentColor: string | null;
  readonly receiptHeader: string | null;
  readonly receiptFooter: string | null;
};

export async function getBrand(): Promise<TenantBrand> {
  return apiFetch<TenantBrand>("/tenant/brand");
}

export async function updateBrand(input: Partial<TenantBrand>): Promise<TenantBrand> {
  return apiFetch<TenantBrand>("/tenant/brand", { method: "PUT", json: input });
}
