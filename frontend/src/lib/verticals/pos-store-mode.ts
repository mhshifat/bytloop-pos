/**
 * Copy and deep links for POS "store mode" and cart — aligned with docs/verticals-coverage.md
 * (Tier A modules vs Tier B profile-only).
 */

import { VerticalProfile } from "@/lib/enums/vertical-profile";

function isFnb(profile: string): boolean {
  return profile.startsWith("fnb_");
}

/**
 * One-line explainer under “Store mode” in POS (truthful; avoids claiming scan rules that do not exist).
 */
export function posStoreModeTagline(profile: string): string {
  if (profile === VerticalProfile.RETAIL_GROCERY) {
    return "Enter runs PLU / weight-barcode and scale flow when the backend returns a match; otherwise barcode or SKU match.";
  }
  if (profile === VerticalProfile.RETAIL_BOOKSTORE) {
    return "Enter looks up an ISBN-10/13; otherwise barcode or SKU match.";
  }
  if (profile === VerticalProfile.RETAIL_APPAREL) {
    return "Enter looks up a variant (barcode/SKU from your matrix); otherwise barcode or SKU on the product.";
  }
  if (profile === VerticalProfile.RETAIL_DEPARTMENT) {
    return "Enter matches barcode or SKU; department metadata is added per line when configured on the product.";
  }
  if (profile === VerticalProfile.RETAIL_PHARMACY) {
    return "Enter matches barcode or SKU; set optional batch ID on a line in the cart for audit. Batches and Rx live under Verticals → Pharmacy.";
  }
  if (isFnb(profile)) {
    return "Enter matches barcode or SKU. Table service and KDS are under Verticals → Restaurant.";
  }
  if (profile === VerticalProfile.HOSPITALITY_RESORT) {
    return "Enter matches barcode or SKU. Resort uses the Hotel module for rooms and reservations; see Verticals → Resort or Hotel.";
  }
  if (profile === VerticalProfile.RETAIL_GENERAL) {
    return "Enter matches barcode or SKU, or pick from the grid.";
  }
  return "Enter matches barcode or SKU, or pick from the grid. Use the matching Verticals module in the sidebar when your industry has one.";
}

export type PosCartQuickLink = { readonly href: string; readonly label: string };

/**
 * Shallow links from POS cart to the Tier A vertical surfaces that match the tenant profile.
 */
export function posCartQuickLinks(profile: string): readonly PosCartQuickLink[] {
  const links: PosCartQuickLink[] = [];
  const push = (href: string, label: string) => {
    if (!links.some((l) => l.href === href)) links.push({ href, label });
  };

  switch (profile) {
    case VerticalProfile.RETAIL_GROCERY:
      push("/verticals/grocery", "PLU & scale");
      break;
    case VerticalProfile.RETAIL_PHARMACY:
      push("/verticals/pharmacy", "Batches & Rx");
      break;
    case VerticalProfile.RETAIL_FURNITURE:
      push("/verticals/furniture", "Custom orders");
      break;
    case VerticalProfile.RETAIL_JEWELRY:
      push("/verticals/jewelry", "Metal rates");
      break;
    case VerticalProfile.RETAIL_THRIFT:
      push("/verticals/consignment", "Consignors & payouts");
      break;
    case VerticalProfile.RETAIL_APPAREL:
      push("/verticals/apparel", "Size/color matrix");
      break;
    case VerticalProfile.RETAIL_BOOKSTORE:
    case VerticalProfile.RETAIL_LIQUOR:
    case VerticalProfile.RETAIL_HARDWARE:
    case VerticalProfile.RETAIL_DEPARTMENT:
    case VerticalProfile.RETAIL_ELECTRONICS:
      // Register-only; no required vertical hub beyond POS
      break;
    default:
      break;
  }

  if (isFnb(profile)) {
    push("/verticals/restaurant/tables", "Tables");
    push("/verticals/restaurant/kds", "Kitchen display");
    push("/verticals/restaurant/routes", "Station routing");
  }
  if (profile === VerticalProfile.HOSPITALITY_HOTEL) {
    push("/verticals/hotel", "Rooms & reservations");
  }
  if (profile === VerticalProfile.HOSPITALITY_RESORT) {
    push("/verticals/resort", "Resort");
    push("/verticals/hotel", "Rooms & reservations");
  }
  if (profile === VerticalProfile.HOSPITALITY_SALON) {
    push("/verticals/salon", "Salon");
  }
  if (profile === VerticalProfile.SERVICES_GARAGE) {
    push("/verticals/garage", "Garage");
  }
  if (profile === VerticalProfile.SERVICES_GYM) {
    push("/verticals/gym", "Gym");
  }
  if (profile === VerticalProfile.SPECIALTY_CINEMA) {
    push("/verticals/cinema", "Cinema");
  }
  if (profile === VerticalProfile.SPECIALTY_RENTAL) {
    push("/verticals/rental", "Rental");
  }

  return links;
}
