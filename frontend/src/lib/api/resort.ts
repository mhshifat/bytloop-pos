import { apiFetch } from "./fetcher";

export type ResortPackage = {
  readonly id: string;
  readonly code: string;
  readonly name: string;
  readonly perNightPriceCents: number;
  readonly includesMeals: boolean;
  readonly includesDrinks: boolean;
  readonly includesSpa: boolean;
  readonly includesActivities: boolean;
};

export type ResortPackageBooking = {
  readonly id: string;
  readonly reservationId: string;
  readonly packageCode: string;
  readonly nights: number;
  readonly totalPackageCents: number;
  readonly attachedAt: string;
};

export type ResortAmenities = {
  readonly reservationId: string;
  readonly packageCode: string;
  readonly includesMeals: boolean;
  readonly includesDrinks: boolean;
  readonly includesSpa: boolean;
  readonly includesActivities: boolean;
};

export async function listPackages(): Promise<readonly ResortPackage[]> {
  return apiFetch<readonly ResortPackage[]>("/resort/packages");
}

export async function createPackage(input: {
  readonly code: string;
  readonly name: string;
  readonly perNightPriceCents: number;
  readonly includesMeals?: boolean;
  readonly includesDrinks?: boolean;
  readonly includesSpa?: boolean;
  readonly includesActivities?: boolean;
}): Promise<ResortPackage> {
  return apiFetch<ResortPackage>("/resort/packages", { method: "POST", json: input });
}

export async function attachPackage(
  reservationId: string,
  input: { readonly packageCode: string; readonly nights: number },
): Promise<ResortPackageBooking> {
  return apiFetch<ResortPackageBooking>(
    `/resort/reservations/${reservationId}/package`,
    { method: "POST", json: input },
  );
}

export async function reservationAmenities(
  reservationId: string,
): Promise<ResortAmenities> {
  return apiFetch<ResortAmenities>(
    `/resort/reservations/${reservationId}/amenities`,
  );
}
