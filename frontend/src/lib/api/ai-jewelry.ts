import { apiFetch } from "./fetcher";

export type JewelryPhotoEstimateRequest = {
  readonly asset: { readonly publicId: string; readonly url: string };
};

export type JewelryPhotoEstimateResponse = {
  readonly karat: number | null;
  readonly grossGrams: string | null;
  readonly netGrams: string | null;
};

export async function estimateJewelryFromPhoto(
  input: JewelryPhotoEstimateRequest,
): Promise<JewelryPhotoEstimateResponse> {
  return apiFetch<JewelryPhotoEstimateResponse>("/ai/jewelry/photo-estimate", {
    method: "POST",
    json: input,
  });
}

