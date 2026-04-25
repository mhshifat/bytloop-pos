import { apiFetch } from "./fetcher";

export type InvoiceStatus = "open" | "paid" | "overdue" | "written_off";

export type WholesaleTier = {
  readonly id: string;
  readonly code: string;
  readonly name: string;
  readonly discountPct: string;
};

export async function listTiers(): Promise<readonly WholesaleTier[]> {
  return apiFetch<readonly WholesaleTier[]>("/wholesale/tiers");
}

export type TierUpsertInput = {
  readonly code: string;
  readonly name: string;
  readonly discountPct: number | string;
};

export async function upsertTier(input: TierUpsertInput): Promise<WholesaleTier> {
  return apiFetch<WholesaleTier>("/wholesale/tiers", {
    method: "PUT",
    json: input,
  });
}

export type WholesaleCustomer = {
  readonly id: string;
  readonly customerId: string;
  readonly tierCode: string | null;
  readonly creditLimitCents: number;
  readonly creditBalanceCents: number;
  readonly netTermsDays: number;
  readonly taxExempt: boolean;
};

export type WholesaleCustomerCreateInput = {
  readonly customerId: string;
  readonly tierCode?: string | null;
  readonly creditLimitCents?: number;
  readonly netTermsDays?: number;
  readonly taxExempt?: boolean;
};

export async function listWholesaleCustomers(): Promise<
  readonly WholesaleCustomer[]
> {
  return apiFetch<readonly WholesaleCustomer[]>("/wholesale/customers");
}

export async function registerWholesaleCustomer(
  input: WholesaleCustomerCreateInput,
): Promise<WholesaleCustomer> {
  return apiFetch<WholesaleCustomer>("/wholesale/customers", {
    method: "POST",
    json: input,
  });
}

export async function getWholesaleCustomer(
  wholesaleCustomerId: string,
): Promise<WholesaleCustomer> {
  return apiFetch<WholesaleCustomer>(
    `/wholesale/customers/${wholesaleCustomerId}`,
  );
}

export type ApplyDiscountResult = {
  readonly subtotalCents: number;
  readonly discountCents: number;
  readonly discountedCents: number;
  readonly tierCode: string | null;
  readonly discountPct: string;
};

export async function applyTierDiscount(input: {
  readonly wholesaleCustomerId: string;
  readonly subtotalCents: number;
}): Promise<ApplyDiscountResult> {
  return apiFetch<ApplyDiscountResult>("/wholesale/apply-discount", {
    method: "POST",
    json: input,
  });
}

export type Invoice = {
  readonly id: string;
  readonly wholesaleCustomerId: string;
  readonly orderId: string;
  readonly invoiceNo: string;
  readonly issuedOn: string;
  readonly dueOn: string;
  readonly status: InvoiceStatus;
  readonly amountCents: number;
  readonly paidCents: number;
};

export async function listInvoices(
  status?: InvoiceStatus,
): Promise<readonly Invoice[]> {
  const sp = new URLSearchParams();
  if (status) sp.set("status", status);
  const q = sp.toString();
  return apiFetch<readonly Invoice[]>(
    `/wholesale/invoices${q ? `?${q}` : ""}`,
  );
}

export async function getInvoice(invoiceId: string): Promise<Invoice> {
  return apiFetch<Invoice>(`/wholesale/invoices/${invoiceId}`);
}

export type InvoiceCreateInput = {
  readonly orderId: string;
  readonly wholesaleCustomerId: string;
  readonly invoiceNo: string;
  readonly issuedOn?: string | null;
};

export async function createInvoice(input: InvoiceCreateInput): Promise<Invoice> {
  return apiFetch<Invoice>("/wholesale/invoices", {
    method: "POST",
    json: input,
  });
}

export async function overdueInvoices(): Promise<readonly Invoice[]> {
  return apiFetch<readonly Invoice[]>("/wholesale/invoices/overdue");
}

export type InvoicePayment = {
  readonly id: string;
  readonly invoiceId: string;
  readonly amountCents: number;
  readonly paidOn: string;
  readonly reference: string | null;
};

export type PaymentCreateInput = {
  readonly amountCents: number;
  readonly paidOn: string;
  readonly reference?: string | null;
};

export async function recordPayment(
  invoiceId: string,
  input: PaymentCreateInput,
): Promise<InvoicePayment> {
  return apiFetch<InvoicePayment>(`/wholesale/invoices/${invoiceId}/payments`, {
    method: "POST",
    json: input,
  });
}

export async function listPayments(
  invoiceId: string,
): Promise<readonly InvoicePayment[]> {
  return apiFetch<readonly InvoicePayment[]>(
    `/wholesale/invoices/${invoiceId}/payments`,
  );
}
