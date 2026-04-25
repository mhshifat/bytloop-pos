"use client";

import {
  Armchair,
  BarChart3,
  Box,
  HandHelping,
  LayoutDashboard,
  PackageSearch,
  Palmtree,
  Route,
  ScrollText,
  Settings,
  Shirt,
  ShoppingCart,
  Sparkles,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { BytloopLogoMark } from "@/components/shared/brand/bytloop-logo";
import { cn } from "@/lib/utils/cn";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/shared/ui/sidebar";

const GROUP_LABEL =
  "h-7 text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-zinc-500";

type NavItem = {
  readonly href: string;
  readonly label: string;
  readonly icon: React.ElementType;
};

const WORKSPACE_NAV: readonly NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/pos", label: "POS terminal", icon: ShoppingCart },
  { href: "/products", label: "Products", icon: PackageSearch },
  { href: "/inventory", label: "Inventory", icon: Box },
  { href: "/orders", label: "Orders", icon: ScrollText },
  { href: "/customers", label: "Customers", icon: Users },
  { href: "/suppliers", label: "Suppliers", icon: Users },
  { href: "/purchase-orders", label: "Purchase orders", icon: ScrollText },
];

const VERTICAL_NAV: readonly NavItem[] = [
  { href: "/verticals/restaurant/kds", label: "Kitchen display", icon: ScrollText },
  { href: "/verticals/restaurant/tables", label: "Tables", icon: Box },
  { href: "/verticals/restaurant/routes", label: "Station routing", icon: Route },
  { href: "/verticals/grocery", label: "Grocery", icon: PackageSearch },
  { href: "/verticals/pharmacy", label: "Pharmacy", icon: PackageSearch },
  { href: "/verticals/garage", label: "Garage", icon: ScrollText },
  { href: "/verticals/gym", label: "Gym", icon: Users },
  { href: "/verticals/salon", label: "Salon", icon: Users },
  { href: "/verticals/hotel", label: "Hotel", icon: Box },
  { href: "/verticals/resort", label: "Resort", icon: Palmtree },
  { href: "/verticals/cinema", label: "Cinema", icon: ScrollText },
  { href: "/verticals/rental", label: "Rental", icon: Box },
  { href: "/verticals/jewelry", label: "Jewelry", icon: PackageSearch },
  { href: "/verticals/apparel", label: "Apparel", icon: Shirt },
  { href: "/verticals/consignment", label: "Consignment", icon: HandHelping },
  { href: "/verticals/furniture", label: "Furniture", icon: Armchair },
];

const REPORTS_NAV: readonly NavItem[] = [
  { href: "/ai-insights", label: "AI insights", icon: Sparkles },
];

const ADMIN_NAV: readonly NavItem[] = [
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/staff", label: "Staff", icon: Users },
  { href: "/audit-log", label: "Audit log", icon: BarChart3 },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <Sidebar>
      <SidebarHeader className="border-b border-sidebar-border/80 px-3 py-2">
        <Link
          href="/"
          className="flex items-center gap-2.5 rounded-md px-1.5 py-1.5 font-semibold tracking-tight text-zinc-50 transition hover:bg-sidebar-accent/60"
        >
          <BytloopLogoMark className="h-7 w-7 shadow-md shadow-primary/25" />
          <span className="text-sm">Bytloop POS</span>
        </Link>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className={cn(GROUP_LABEL)}>Workspace</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {WORKSPACE_NAV.map((item) => (
                <NavRow key={item.href} item={item} active={pathname.startsWith(item.href)} />
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarGroup>
          <SidebarGroupLabel className={cn(GROUP_LABEL)}>Verticals</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {VERTICAL_NAV.map((item) => (
                <NavRow key={item.href} item={item} active={pathname.startsWith(item.href)} />
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarGroup>
          <SidebarGroupLabel className={cn(GROUP_LABEL)}>Reports</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {REPORTS_NAV.map((item) => (
                <NavRow key={item.href} item={item} active={pathname.startsWith(item.href)} />
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarGroup>
          <SidebarGroupLabel className={cn(GROUP_LABEL)}>Admin</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {ADMIN_NAV.map((item) => (
                <NavRow key={item.href} item={item} active={pathname.startsWith(item.href)} />
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter />
    </Sidebar>
  );
}

function NavRow({ item, active }: { readonly item: NavItem; readonly active: boolean }) {
  const Icon = item.icon;
  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild isActive={active}>
        <Link href={item.href}>
          <Icon aria-hidden="true" />
          <span>{item.label}</span>
        </Link>
      </SidebarMenuButton>
    </SidebarMenuItem>
  );
}
