import { apiFetch } from "./fetcher";

export type TranslateRequest = {
  readonly sourceText: string;
  readonly targetLocale: string;
};

export type TranslateResponse = {
  readonly translatedText: string;
  readonly cached: boolean;
};

export async function translateText(input: TranslateRequest): Promise<TranslateResponse> {
  return apiFetch<TranslateResponse>("/ai/translate", { method: "POST", json: input });
}

