import { apiFetch } from "./fetcher";

export type TruckLocation = {
  readonly id: string;
  readonly locationName: string;
  readonly latitude: string;
  readonly longitude: string;
  readonly startsAt: string;
  readonly endsAt: string;
  readonly notes: string | null;
  readonly createdAt: string;
};

export type DailyMenuItem = {
  readonly id: string;
  readonly menuId: string;
  readonly productId: string;
  readonly dailyPriceCentsOverride: number | null;
  readonly soldOut: boolean;
  readonly sortOrder: number;
};

export type DailyMenu = {
  readonly id: string;
  readonly menuDate: string;
  readonly notes: string | null;
  readonly publishedAt: string;
  readonly items: readonly DailyMenuItem[];
};

export type SetLocationInput = {
  readonly locationName: string;
  readonly latitude: string | number;
  readonly longitude: string | number;
  readonly startsAt: string;
  readonly endsAt: string;
  readonly notes?: string | null;
};

export async function setLocation(input: SetLocationInput): Promise<TruckLocation> {
  return apiFetch<TruckLocation>("/food-truck/locations", {
    method: "POST",
    json: input,
  });
}

export async function listLocations(
  upcomingOnly = false,
): Promise<readonly TruckLocation[]> {
  const qs = upcomingOnly ? "?upcomingOnly=true" : "";
  return apiFetch<readonly TruckLocation[]>(`/food-truck/locations${qs}`);
}

export async function currentLocation(): Promise<TruckLocation | null> {
  return apiFetch<TruckLocation | null>("/food-truck/locations/current");
}

export type PublishMenuItemInput = {
  readonly productId: string;
  readonly dailyPriceCentsOverride?: number | null;
  readonly soldOut?: boolean;
  readonly sortOrder?: number;
};

export type PublishMenuInput = {
  readonly menuDate: string;
  readonly notes?: string | null;
  readonly items: readonly PublishMenuItemInput[];
};

export async function publishMenu(input: PublishMenuInput): Promise<DailyMenu> {
  return apiFetch<DailyMenu>("/food-truck/menus", { method: "POST", json: input });
}

export async function todayMenu(): Promise<DailyMenu> {
  return apiFetch<DailyMenu>("/food-truck/menus/today");
}

export async function markSoldOut(
  itemId: string,
  soldOut: boolean,
): Promise<DailyMenuItem> {
  return apiFetch<DailyMenuItem>(`/food-truck/menu-items/${itemId}/sold-out`, {
    method: "PATCH",
    json: { soldOut },
  });
}
