"use client";

import { WelcomeCard } from "@/components/dashboard/WelcomeCard";
import { ActiveMaps } from "@/components/dashboard/ActiveMaps";
import { ActionsPanel } from "@/components/dashboard/ActionsPanel";
import { NotificationsPanel } from "@/components/dashboard/NotificationsPanel";

export default function DeveloperDashboard() {
  return (
    <div className="space-y-6">
      <div className="grid md:grid-cols-3 gap-4">
        <div className="md:col-span-2">
          <WelcomeCard />
        </div>
        <div className="md:col-span-1">
          <ActionsPanel />
        </div>
      </div>

      <ActiveMaps />

      <div className="grid md:grid-cols-3 gap-4">
        <div className="md:col-span-2">
          {/* Main developer content placeholder */}
        </div>
        <div>
          <NotificationsPanel />
        </div>
      </div>
    </div>
  );
}
