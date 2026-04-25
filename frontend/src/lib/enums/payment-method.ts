import type { PaymentMethod } from "@/lib/api/sales";

const LABELS: Record<PaymentMethod, string> = {
  cash: "Cash",
  card: "Card",
  bkash: "bKash",
  nagad: "Nagad",
  sslcommerz: "SSLCommerz",
  rocket: "Rocket",
  stripe: "Stripe",
  paypal: "PayPal",
};

export function paymentMethodLabel(method: string): string {
  return LABELS[method as PaymentMethod] ?? method;
}
