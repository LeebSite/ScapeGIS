"use client";

import { AdminStats } from "@/components/dashboard/AdminStats";
import { PendingMapRequests } from "@/components/dashboard/PendingMapRequests";
import { RecentProcessing } from "@/components/dashboard/RecentProcessing";

export default function AdminDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Beranda Admin</h2>
        <p className="text-muted-foreground">Ringkasan platform dan manajemen</p>
      </div>

      <AdminStats />

      <div className="grid md:grid-cols-3 gap-4">
        <div className="md:col-span-2">
          <PendingMapRequests />
          <RecentProcessing />
        </div>
        <div>
          {/* Right column for quick actions or alerts */}
        </div>
      </div>
    </div>
  );
}
