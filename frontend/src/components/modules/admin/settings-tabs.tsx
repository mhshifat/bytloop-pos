"use client";

import { BrandSection } from "@/components/modules/admin/brand-section";
import { CategoriesSection } from "@/components/modules/admin/categories-section";
import { DiscountsSection } from "@/components/modules/admin/discounts-section";
import { LocationsSection } from "@/components/modules/admin/locations-section";
import { TaxRulesSection } from "@/components/modules/admin/tax-rules-section";
import { TenantSection } from "@/components/modules/admin/tenant-section";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/shared/ui/tabs";

const tabs = [
  { value: "workspace", label: "Workspace" },
  { value: "brand", label: "Brand" },
  { value: "locations", label: "Locations" },
  { value: "categories", label: "Categories" },
  { value: "tax", label: "Tax rules" },
  { value: "discounts", label: "Discounts" },
] as const;

export function SettingsTabs() {
  return (
    <Tabs defaultValue="workspace" className="w-full space-y-6">
      <div className="w-full overflow-x-auto [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        <TabsList className="flex h-auto min-h-9 w-full flex-wrap justify-start gap-1 border border-zinc-600/50 bg-zinc-900/90 p-1 shadow-sm sm:inline-flex sm:w-max sm:max-w-full sm:flex-nowrap">
          {tabs.map((t) => (
            <TabsTrigger
              key={t.value}
              value={t.value}
              className="shrink-0 px-3 py-2 text-zinc-200/95 hover:text-white data-[state=active]:border data-[state=active]:border-zinc-500/60 data-[state=active]:bg-zinc-800 data-[state=active]:text-white data-[state=active]:shadow-md dark:text-zinc-200 dark:hover:text-white dark:data-[state=active]:bg-zinc-800 dark:data-[state=active]:text-white"
            >
              {t.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </div>

      <TabsContent value="workspace" className="mt-0">
        <TenantSection />
      </TabsContent>
      <TabsContent value="brand" className="mt-0">
        <BrandSection />
      </TabsContent>
      <TabsContent value="locations" className="mt-0">
        <LocationsSection />
      </TabsContent>
      <TabsContent value="categories" className="mt-0">
        <CategoriesSection />
      </TabsContent>
      <TabsContent value="tax" className="mt-0">
        <TaxRulesSection />
      </TabsContent>
      <TabsContent value="discounts" className="mt-0">
        <DiscountsSection />
      </TabsContent>
    </Tabs>
  );
}
