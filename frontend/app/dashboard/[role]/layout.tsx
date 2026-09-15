"use client";

import { useParams } from "next/navigation";
import { ProtectedRoute } from "@/components/protected-route";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { useAuthStore } from "@/lib/store";
import { useSidebarStore } from "@/lib/store";
import type { UserRole } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const params = useParams();
  const role = params.role as UserRole;
  const { user } = useAuthStore();
  const { isCollapsed } = useSidebarStore();

  return (
    <ProtectedRoute allowedRoles={role === "admin" ? ["admin"] : ["developer"]}>
      <div className="flex h-screen overflow-hidden">
        {user && <Sidebar role={user.role} />}
        <div 
          className={cn(
            "flex flex-1 flex-col overflow-hidden transition-all duration-300",
            isCollapsed ? "ml-0" : "ml-0"
          )}
        >
          <Header />
          <main className="flex-1 overflow-y-auto bg-muted/50 p-6">
            {children}
          </main>
        </div>
      </div>
    </ProtectedRoute>
  );
}

