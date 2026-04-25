import { apiFetch } from "./fetcher";

export type TableStatus = "available" | "occupied" | "reserved" | "cleaning";

export type RestaurantTable = {
  readonly id: string;
  readonly code: string;
  readonly label: string;
  readonly seats: number;
  readonly status: TableStatus;
  readonly currentOrderId: string | null;
};

export async function listTables(): Promise<readonly RestaurantTable[]> {
  return apiFetch<readonly RestaurantTable[]>("/restaurant/tables");
}

export type CreateTableInput = {
  readonly code: string;
  readonly label: string;
  readonly seats: number;
};

export async function createTable(input: CreateTableInput): Promise<RestaurantTable> {
  return apiFetch<RestaurantTable>("/restaurant/tables", {
    method: "POST",
    json: input,
  });
}
