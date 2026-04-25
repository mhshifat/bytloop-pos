import { apiFetch } from "./fetcher";

export type BookLookupResult = {
  readonly id: string;
  readonly name: string;
  readonly sku: string;
  readonly priceCents: number;
  readonly currency: string;
};

export async function lookupIsbn(isbn: string): Promise<BookLookupResult> {
  return apiFetch<BookLookupResult>(
    `/bookstore/lookup/${encodeURIComponent(isbn)}`,
  );
}
