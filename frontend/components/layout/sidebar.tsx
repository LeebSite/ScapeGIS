"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
// use native img for logos to avoid Next/Image optimization issues
import { cn } from "@/lib/utils";
import { useSidebarStore } from "@/lib/store";
import { getNavItems } from "@/lib/nav";
import { useAuthStore } from "@/lib/store";
import {
  LayoutDashboard,
  Map,
  Settings,
  CreditCard,
  Users,
  BarChart3,
  FolderKanban,
  ChevronLeft,
  ChevronRight,
  Database,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import type { UserRole } from "@/lib/types";

interface SidebarProps {
  role?: UserRole;
}

const adminNavItems = [
  { href: "/dashboard/admin", label: "Beranda", icon: LayoutDashboard },
  { href: "/dashboard/admin/projects", label: "Proyek", icon: FolderKanban },
  { href: "/dashboard/admin/maps", label: "Peta Aktif", icon: Map },
  { href: "/dashboard/admin/gis-datasets", label: "GIS Dataset", icon: Database },
  { href: "/dashboard/admin/users", label: "Pengguna", icon: Users },
  { href: "/dashboard/admin/analytics", label: "Analitik", icon: BarChart3 },
  { href: "/dashboard/admin/settings", label: "Pengaturan", icon: Settings },
];

const developerNavItems = [
  { href: "/dashboard/developer", label: "Beranda", icon: LayoutDashboard },
  { href: "/dashboard/developer/projects", label: "Proyek", icon: FolderKanban },
  { href: "/dashboard/developer/subscription", label: "Langganan", icon: CreditCard },
  { href: "/dashboard/developer/settings", label: "Pengaturan", icon: Settings },
];

export function Sidebar({ role }: SidebarProps) {
  const pathname = usePathname();
  const { isCollapsed, toggleSidebar } = useSidebarStore();
  const { user } = useAuthStore();
  const resolvedRole = role ?? (user?.role as UserRole) ?? "developer";

  // Use local nav config instead of getNavItems to ensure translation
  const navItems = resolvedRole === 'admin' ? adminNavItems : developerNavItems;

  const isActivePath = (href: string) =>
    pathname.split(/[?#]/)[0] === href;

  return (
    <aside
      className={cn(
        "flex h-full flex-col border-r bg-card transition-all duration-300 shadow-sm",
        isCollapsed ? "w-16" : "w-64"
      )}
      aria-label="Navigasi Utama"
    >
      {/* ================= HEADER ================= */}
      <div className="flex h-16 items-center border-b px-4">
        {!isCollapsed ? (
          <div className="flex w-full items-center justify-between">
            {/* Logo + Brand */}
            <div className="flex items-center gap-3">
              <img
                src="/img/logo_scapegis.svg"
                alt="Scapegis Logo"
                width={36}
                height={36}
                className="block"
              />
              <div className="flex flex-col">
                <span className="font-kayak text-lg md:text-xl tracking-wide font-semibold text-[#01123E]">
                  Scapegis
                </span>
                <span className="text-xs text-muted-foreground">
                  {resolvedRole === "admin" ? "Administrator" : "Pengembang"}
                </span>
              </div>
            </div>

            {/* Collapse */}
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={toggleSidebar}
              title="Collapse sidebar"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          /* Collapsed: Logo only */
          <div className="flex w-full justify-center">
            <img
              src="/img/logo_scapegis.svg"
              alt="Scapegis Logo"
              width={32}
              height={32}
              className="block"
            />
          </div>
        )}
      </div>

      {/* Expand Button */}
      {isCollapsed && (
        <div className="border-b px-2 py-2">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-full"
            onClick={toggleSidebar}
            title="Expand sidebar"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* ================= NAVIGATION ================= */}
      <nav className="flex-1 space-y-1 p-3" aria-label="Sidebar">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = isActivePath(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              title={isCollapsed ? item.label : ""}
              className={cn(
                "group relative flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-primary text-primary-foreground shadow-md"
                  : "text-muted-foreground hover:bg-transparent hover:text-primary hover:ring-1 hover:ring-primary/50",
                isCollapsed ? "justify-center" : "gap-3"
              )}
            >
              <Icon
                className={cn(
                  "h-5 w-5 shrink-0 transition-colors",
                  isActive ? "text-primary-foreground" : "text-muted-foreground group-hover:text-primary"
                )}
              />

              <span
                className={cn(
                  "whitespace-nowrap transition-all",
                  isCollapsed
                    ? "w-0 overflow-hidden opacity-0"
                    : "opacity-100"
                )}
              >
                {item.label}
              </span>

              {/* Tooltip (collapsed) */}
              {isCollapsed && (
                <span className="pointer-events-none absolute left-full ml-2 rounded-md bg-popover px-2 py-1 text-sm text-popover-foreground opacity-0 shadow-md transition-opacity group-hover:opacity-100">
                  {item.label}
                </span>
              )}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
