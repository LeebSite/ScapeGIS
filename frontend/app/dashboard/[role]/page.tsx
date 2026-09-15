"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store";
import { getDashboardRoute } from "@/lib/utils";

export default function DashboardRedirect() {
  const { user } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    const role = user?.role ?? "developer";
    const route = getDashboardRoute(role);
    router.replace(route);
  }, [user, router]);

  return null;
}

