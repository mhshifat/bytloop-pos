import { apiFetch } from "./fetcher";

export type IdScanRequest = {
  readonly asset: { readonly publicId: string; readonly url: string };
};

export type IdScanResponse = {
  readonly customerDob: string;
};

export async function scanIdForDob(input: IdScanRequest): Promise<IdScanResponse> {
  return apiFetch<IdScanResponse>("/ai/age-restricted/id-scan", { method: "POST", json: input });
}

