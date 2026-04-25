import { apiFetch } from "./fetcher";

export type FuelType = "regular" | "premium" | "diesel" | "cng";
export type DispenserStatus = "active" | "maintenance";

export type FuelDispenser = {
  readonly id: string;
  readonly label: string;
  readonly fuelType: FuelType;
  readonly pricePerLiterCents: number;
  readonly productId: string | null;
  readonly status: DispenserStatus;
};

export type DispenserReading = {
  readonly id: string;
  readonly dispenserId: string;
  readonly totalizerReading: number;
  readonly litersDispensed: number;
  readonly orderId: string | null;
  readonly takenAt: string;
};

export async function listDispensers(): Promise<readonly FuelDispenser[]> {
  return apiFetch<readonly FuelDispenser[]>("/gas-station/dispensers");
}

export async function createDispenser(input: {
  readonly label: string;
  readonly fuelType: FuelType;
  readonly pricePerLiterCents: number;
  readonly productId?: string | null;
}): Promise<FuelDispenser> {
  return apiFetch<FuelDispenser>("/gas-station/dispensers", {
    method: "POST",
    json: { ...input, productId: input.productId ?? null },
  });
}

export async function recordReading(input: {
  readonly dispenserId: string;
  readonly totalizerReading: number;
}): Promise<DispenserReading> {
  return apiFetch<DispenserReading>("/gas-station/readings", {
    method: "POST",
    json: input,
  });
}

export async function listReadings(
  dispenserId: string,
): Promise<readonly DispenserReading[]> {
  return apiFetch<readonly DispenserReading[]>(
    `/gas-station/dispensers/${dispenserId}/readings`,
  );
}
