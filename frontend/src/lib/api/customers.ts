import { apiFetch } from "./fetcher";

export type Customer = {
  readonly id: string;
  readonly firstName: string;
  readonly lastName: string;
  readonly email: string | null;
  readonly phone: string | null;
  readonly notes: string | null;
};

export type CustomerList = {
  readonly items: readonly Customer[];
  readonly hasMore: boolean;
  readonly page: number;
  readonly pageSize: number;
};

export async function listCustomers(params: {
  readonly search?: string;
  readonly page?: number;
  readonly pageSize?: number;
} = {}): Promise<CustomerList> {
  const sp = new URLSearchParams();
  if (params.search) sp.set("search", params.search);
  if (params.page) sp.set("page", String(params.page));
  if (params.pageSize) sp.set("pageSize", String(params.pageSize));
  const q = sp.toString();
  return apiFetch<CustomerList>(`/customers${q ? `?${q}` : ""}`);
}

export type CustomerCreateInput = {
  readonly firstName: string;
  readonly lastName?: string;
  readonly email?: string;
  readonly phone?: string;
  readonly notes?: string;
};

export async function createCustomer(input: CustomerCreateInput): Promise<Customer> {
  return apiFetch<Customer>("/customers", { method: "POST", json: input });
}

export async function getCustomer(customerId: string): Promise<Customer> {
  return apiFetch<Customer>(`/customers/${customerId}`);
}

export type CustomerUpdateInput = {
  readonly firstName?: string;
  readonly lastName?: string;
  readonly email?: string | null;
  readonly phone?: string | null;
  readonly notes?: string | null;
};

export async function updateCustomer(
  customerId: string,
  input: CustomerUpdateInput,
): Promise<Customer> {
  return apiFetch<Customer>(`/customers/${customerId}`, {
    method: "PATCH",
    json: input,
  });
}
