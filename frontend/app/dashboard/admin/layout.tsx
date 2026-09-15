"use client";

import { ProtectedRoute } from "@/components/protected-route";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { useAuthStore } from "@/lib/store";
import { useSidebarStore } from "@/lib/store";
import { cn } from "@/lib/utils";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user } = useAuthStore();
  const { isCollapsed } = useSidebarStore();

  return (
    <ProtectedRoute allowedRoles={["admin"]}>
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

