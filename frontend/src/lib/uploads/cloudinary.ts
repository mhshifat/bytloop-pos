import { signUpload } from "@/lib/api/media";

export const MAX_UPLOAD_BYTES = 95 * 1024 * 1024;

export type UploadedAsset = {
  readonly publicId: string;
  readonly secureUrl: string;
  readonly bytes: number;
  readonly width?: number;
  readonly height?: number;
};

export async function uploadImageToCloudinary(input: {
  readonly purpose:
    | "invoice_ocr"
    | "id_scan"
    | "shelf_audit"
    | "planogram"
    | "jewelry"
    | "cafeteria";
  readonly file: File;
}): Promise<UploadedAsset> {
  const { file, purpose } = input;
  if (file.size > MAX_UPLOAD_BYTES) {
    throw new Error("File too large (max 95MB).");
  }
  if (!file.type.startsWith("image/")) {
    throw new Error("Only image uploads are supported.");
  }

  const signed = await signUpload({ purpose, contentType: file.type, bytes: file.size });
  const form = new FormData();
  for (const [k, v] of Object.entries(signed.fields)) form.set(k, v);
  form.set("file", file);

  const res = await fetch(signed.uploadUrl, { method: "POST", body: form });
  if (!res.ok) {
    const t = await res.text().catch(() => "");
    throw new Error(`Upload failed (${res.status}): ${t || res.statusText}`);
  }
  const json = (await res.json()) as any;
  return {
    publicId: String(json.public_id ?? signed.publicId),
    secureUrl: String(json.secure_url ?? json.url ?? ""),
    bytes: Number(json.bytes ?? file.size),
    width: json.width != null ? Number(json.width) : undefined,
    height: json.height != null ? Number(json.height) : undefined,
  };
}

