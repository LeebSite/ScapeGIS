"use client";

import { useParams } from "next/navigation";
import { MapComponent } from "@/components/gis/map-component";
import { SpatialAIPanel } from "@/components/ai/spatial-ai-panel";

export default function AdminProjectDetailPage() {
  const params = useParams();
  const projectId = params.projectId as string;

  return (
    <div className="h-[calc(100vh-120px)] flex gap-4 -mx-6 -mb-6">
      {/* Map View - Central Area */}
      <div className="flex-1 min-w-0">
        <div className="h-full rounded-lg border bg-card overflow-hidden">
          <MapComponent />
        </div>
      </div>

      {/* AI Panel - Right Side */}
      <div className="w-80 flex-shrink-0">
        <SpatialAIPanel className="h-full" />
      </div>
    </div>
  );
}

