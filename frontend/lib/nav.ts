import type { UserRole } from "./types";
import {
  LayoutDashboard,
  Map,
  Settings,
  CreditCard,
  Users,
  FolderKanban,
  Database,
} from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: (props: any) => JSX.Element;
}

export const adminNavItems: NavItem[] = [
  { href: "/dashboard/admin", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/admin/users", label: "Users", icon: Users },
  { href: "/dashboard/admin/subscriptions", label: "Subscriptions", icon: CreditCard },
  { href: "/dashboard/admin/map-requests", label: "Map Requests", icon: Map },
  { href: "/dashboard/admin/gis-datasets", label: "GIS Datasets", icon: Database },
  { href: "/dashboard/admin/settings", label: "Settings", icon: Settings },
];

export const developerNavItems: NavItem[] = [
  { href: "/dashboard/developer", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/developer/projects", label: "Projects", icon: FolderKanban },
  { href: "/dashboard/developer/subscription", label: "Subscription", icon: CreditCard },
  { href: "/dashboard/developer/settings", label: "Settings", icon: Settings },
];

export function getNavItems(role: UserRole) {
  return role === "admin" ? adminNavItems : developerNavItems;
}
