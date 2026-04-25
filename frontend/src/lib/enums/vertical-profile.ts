/**
 * Vertical profiles — mirrors ``backend/src/modules/tenants/entity.py``.
 * Drives UX hints in the POS (which buttons to hide, which labels to swap).
 * Labels are user-visible so we never render the raw enum value.
 */

export const VerticalProfile = {
  RETAIL_GENERAL: "retail_general",
  RETAIL_ELECTRONICS: "retail_electronics",
  RETAIL_APPAREL: "retail_apparel",
  RETAIL_GROCERY: "retail_grocery",
  RETAIL_PHARMACY: "retail_pharmacy",
  RETAIL_JEWELRY: "retail_jewelry",
  RETAIL_FURNITURE: "retail_furniture",
  RETAIL_BOOKSTORE: "retail_bookstore",
  RETAIL_LIQUOR: "retail_liquor",
  RETAIL_CANNABIS: "retail_cannabis",
  RETAIL_FLORIST: "retail_florist",
  RETAIL_THRIFT: "retail_thrift",
  RETAIL_PET_STORE: "retail_pet_store",
  RETAIL_HARDWARE: "retail_hardware",
  RETAIL_DEPARTMENT: "retail_department",

  FNB_RESTAURANT: "fnb_restaurant",
  FNB_QSR: "fnb_qsr",
  FNB_CAFE: "fnb_cafe",
  FNB_BAR: "fnb_bar",
  FNB_FOOD_TRUCK: "fnb_food_truck",
  FNB_BAKERY: "fnb_bakery",
  FNB_PIZZA: "fnb_pizza",
  FNB_CLOUD_KITCHEN: "fnb_cloud_kitchen",
  FNB_CAFETERIA: "fnb_cafeteria",

  HOSPITALITY_HOTEL: "hospitality_hotel",
  HOSPITALITY_RESORT: "hospitality_resort",
  HOSPITALITY_SALON: "hospitality_salon",
  HOSPITALITY_EVENT: "hospitality_event",
  HOSPITALITY_THEME_PARK: "hospitality_theme_park",

  SERVICES_GARAGE: "services_garage",
  SERVICES_GAS_STATION: "services_gas_station",
  SERVICES_CAR_WASH: "services_car_wash",
  SERVICES_LAUNDRY: "services_laundry",
  SERVICES_GYM: "services_gym",
  SERVICES_MEDICAL: "services_medical",
  SERVICES_VETERINARY: "services_veterinary",

  SPECIALTY_MUSEUM: "specialty_museum",
  SPECIALTY_CINEMA: "specialty_cinema",
  SPECIALTY_WHOLESALE: "specialty_wholesale",
  SPECIALTY_RENTAL: "specialty_rental",
  SPECIALTY_MARKET: "specialty_market",
  SPECIALTY_NONPROFIT: "specialty_nonprofit",
} as const;

export type VerticalProfile = (typeof VerticalProfile)[keyof typeof VerticalProfile];

type Group = {
  readonly label: string;
  readonly options: readonly { readonly value: VerticalProfile; readonly label: string }[];
};

export const VERTICAL_GROUPS: readonly Group[] = [
  {
    label: "Retail",
    options: [
      { value: VerticalProfile.RETAIL_GENERAL, label: "General retail" },
      { value: VerticalProfile.RETAIL_APPAREL, label: "Apparel" },
      { value: VerticalProfile.RETAIL_GROCERY, label: "Grocery" },
      { value: VerticalProfile.RETAIL_PHARMACY, label: "Pharmacy" },
      { value: VerticalProfile.RETAIL_JEWELRY, label: "Jewelry" },
      { value: VerticalProfile.RETAIL_ELECTRONICS, label: "Electronics" },
      { value: VerticalProfile.RETAIL_FURNITURE, label: "Furniture" },
      { value: VerticalProfile.RETAIL_BOOKSTORE, label: "Bookstore" },
      { value: VerticalProfile.RETAIL_LIQUOR, label: "Liquor / Tobacco" },
      { value: VerticalProfile.RETAIL_CANNABIS, label: "Cannabis / Dispensary" },
      { value: VerticalProfile.RETAIL_FLORIST, label: "Florist" },
      { value: VerticalProfile.RETAIL_THRIFT, label: "Thrift / Consignment" },
      { value: VerticalProfile.RETAIL_PET_STORE, label: "Pet store" },
      { value: VerticalProfile.RETAIL_HARDWARE, label: "Hardware" },
      { value: VerticalProfile.RETAIL_DEPARTMENT, label: "Department store" },
    ],
  },
  {
    label: "Food & beverage",
    options: [
      { value: VerticalProfile.FNB_RESTAURANT, label: "Restaurant" },
      { value: VerticalProfile.FNB_QSR, label: "Quick service (QSR)" },
      { value: VerticalProfile.FNB_CAFE, label: "Café" },
      { value: VerticalProfile.FNB_BAR, label: "Bar / Pub / Nightclub" },
      { value: VerticalProfile.FNB_FOOD_TRUCK, label: "Food truck" },
      { value: VerticalProfile.FNB_BAKERY, label: "Bakery" },
      { value: VerticalProfile.FNB_PIZZA, label: "Pizza" },
      { value: VerticalProfile.FNB_CLOUD_KITCHEN, label: "Cloud kitchen" },
      { value: VerticalProfile.FNB_CAFETERIA, label: "Cafeteria" },
    ],
  },
  {
    label: "Hospitality",
    options: [
      { value: VerticalProfile.HOSPITALITY_HOTEL, label: "Hotel" },
      { value: VerticalProfile.HOSPITALITY_RESORT, label: "Resort" },
      { value: VerticalProfile.HOSPITALITY_SALON, label: "Salon / Spa" },
      { value: VerticalProfile.HOSPITALITY_EVENT, label: "Event / Venue" },
      { value: VerticalProfile.HOSPITALITY_THEME_PARK, label: "Theme park" },
    ],
  },
  {
    label: "Services",
    options: [
      { value: VerticalProfile.SERVICES_GARAGE, label: "Garage / Auto repair" },
      { value: VerticalProfile.SERVICES_GAS_STATION, label: "Gas station" },
      { value: VerticalProfile.SERVICES_CAR_WASH, label: "Car wash" },
      { value: VerticalProfile.SERVICES_LAUNDRY, label: "Laundry / Dry cleaning" },
      { value: VerticalProfile.SERVICES_GYM, label: "Gym / Fitness" },
      { value: VerticalProfile.SERVICES_MEDICAL, label: "Medical / Dental" },
      { value: VerticalProfile.SERVICES_VETERINARY, label: "Veterinary" },
    ],
  },
  {
    label: "Specialty",
    options: [
      { value: VerticalProfile.SPECIALTY_MUSEUM, label: "Museum / Gallery" },
      { value: VerticalProfile.SPECIALTY_CINEMA, label: "Cinema / Theater" },
      { value: VerticalProfile.SPECIALTY_WHOLESALE, label: "Wholesale / B2B" },
      { value: VerticalProfile.SPECIALTY_RENTAL, label: "Rental" },
      { value: VerticalProfile.SPECIALTY_MARKET, label: "Market / Pop-up" },
      { value: VerticalProfile.SPECIALTY_NONPROFIT, label: "Non-profit" },
    ],
  },
];

const LABELS: Record<string, string> = Object.fromEntries(
  VERTICAL_GROUPS.flatMap((g) => g.options.map((o) => [o.value, o.label])),
);

export function verticalProfileLabel(value: string): string {
  return LABELS[value] ?? value;
}
