import { apiFetch } from "./fetcher";

export type VoiceProductDraftRequest = {
  readonly transcript: string;
};

export type VoiceProductDraft = {
  readonly sku: string | null;
  readonly barcode: string | null;
  readonly name: string;
  readonly description: string | null;
  readonly categoryName: string | null;
  readonly priceCents: number;
  readonly currency: string;
};

export async function voiceProductDraft(
  input: VoiceProductDraftRequest,
): Promise<VoiceProductDraft> {
  return apiFetch<VoiceProductDraft>("/ai/catalog/voice-product", {
    method: "POST",
    json: input,
  });
}

