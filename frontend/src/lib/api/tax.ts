import { apiFetch } from "./fetcher";

export type TaxRule = {
  readonly id: string;
  readonly code: string;
  readonly name: string;
  readonly rate: string;
  readonly isInclusive: boolean;
  readonly isActive: boolean;
};

export async function listTaxRules(): Promise<readonly TaxRule[]> {
  return apiFetch<readonly TaxRule[]>("/tax-rules");
}

export type TaxRuleCreate = {
  readonly code: string;
  readonly name: string;
  readonly rate: string;
  readonly isInclusive: boolean;
};

export async function createTaxRule(input: TaxRuleCreate): Promise<TaxRule> {
  return apiFetch<TaxRule>("/tax-rules", { method: "POST", json: input });
}
