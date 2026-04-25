import { apiFetch } from "./fetcher";

export type PetProductMetadata = {
  readonly productId: string;
  readonly targetSpecies: string | null;
  readonly targetBreed: string | null;
  readonly lifeStage: string | null;
  readonly weightRangeLbs: string | null;
  readonly isPrescriptionFood: boolean;
};

export type UpsertMetadataInput = {
  readonly productId: string;
  readonly targetSpecies?: string | null;
  readonly targetBreed?: string | null;
  readonly lifeStage?: string | null;
  readonly weightRangeLbs?: string | null;
  readonly isPrescriptionFood?: boolean;
};

export async function upsertMetadata(
  input: UpsertMetadataInput,
): Promise<PetProductMetadata> {
  return apiFetch<PetProductMetadata>("/pet-store/metadata", {
    method: "PUT",
    json: input,
  });
}

export async function listBySpecies(
  species: string,
): Promise<readonly PetProductMetadata[]> {
  return apiFetch<readonly PetProductMetadata[]>(
    `/pet-store/by-species/${encodeURIComponent(species)}`,
  );
}

export async function listPrescriptionFoods(): Promise<
  readonly PetProductMetadata[]
> {
  return apiFetch<readonly PetProductMetadata[]>(
    "/pet-store/prescription-foods",
  );
}
