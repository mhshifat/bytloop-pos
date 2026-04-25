import { apiFetch } from "./fetcher";

export type Category = {
  readonly id: string;
  readonly slug: string;
  readonly name: string;
  readonly parentId: string | null;
};

export async function listCategories(): Promise<readonly Category[]> {
  return apiFetch<readonly Category[]>("/categories");
}

export type CategoryCreateInput = {
  readonly slug: string;
  readonly name: string;
  readonly parentId?: string | null;
};

export async function createCategory(input: CategoryCreateInput): Promise<Category> {
  return apiFetch<Category>("/categories", { method: "POST", json: input });
}
