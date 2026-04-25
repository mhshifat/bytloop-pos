import { apiFetch } from "./fetcher";

export type Location = {
  readonly id: string;
  readonly code: string;
  readonly name: string;
};

export async function listLocations(): Promise<readonly Location[]> {
  return apiFetch<readonly Location[]>("/locations");
}

export async function createLocation(input: {
  readonly code: string;
  readonly name: string;
}): Promise<Location> {
  return apiFetch<Location>("/locations", { method: "POST", json: input });
}
