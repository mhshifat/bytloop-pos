import { apiFetch } from "./fetcher";

export type UploadSignRequest = {
  readonly purpose:
    | "invoice_ocr"
    | "id_scan"
    | "shelf_audit"
    | "planogram"
    | "jewelry"
    | "cafeteria";
  readonly contentType: string;
  readonly bytes: number;
};

export type UploadSignResponse = {
  readonly uploadUrl: string;
  readonly fields: Record<string, string>;
  readonly publicId: string;
  readonly maxBytes: number;
};

export async function signUpload(input: UploadSignRequest): Promise<UploadSignResponse> {
  return apiFetch<UploadSignResponse>("/media/uploads/sign", { method: "POST", json: input });
}

