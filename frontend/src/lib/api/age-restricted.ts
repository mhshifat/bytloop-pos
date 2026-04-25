import { apiFetch } from "./fetcher";

export type AgeRestrictedProduct = {
  readonly productId: string;
  readonly minAgeYears: number;
};

export type RequiresVerificationItem = {
  readonly productId: string;
  readonly minAgeYears: number;
};

export type AgeVerificationLog = {
  readonly id: string;
  readonly orderId: string | null;
  readonly verifiedByUserId: string | null;
  readonly customerDob: string;
  readonly minAgeRequired: number;
  readonly verifiedAgeYears: number;
  readonly createdAt: string;
};

export async function setMinAge(input: {
  readonly productId: string;
  readonly minAgeYears: number;
}): Promise<AgeRestrictedProduct> {
  return apiFetch<AgeRestrictedProduct>("/age-restricted/products", {
    method: "PUT",
    json: input,
  });
}

export async function requiresVerification(
  productIds: readonly string[],
): Promise<readonly RequiresVerificationItem[]> {
  return apiFetch<readonly RequiresVerificationItem[]>(
    "/age-restricted/requires-verification",
    { method: "POST", json: { productIds } },
  );
}

export type VerifyInput = {
  readonly orderId: string;
  readonly customerDob: string;
  readonly verifiedByUserId: string;
};

export async function verify(input: VerifyInput): Promise<AgeVerificationLog> {
  return apiFetch<AgeVerificationLog>("/age-restricted/verify", {
    method: "POST",
    json: input,
  });
}
