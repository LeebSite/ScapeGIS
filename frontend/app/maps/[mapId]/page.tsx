"use client";

import { useRouter, useParams } from "next/navigation";
import { isMapActive, getMapById } from "@/lib/maps";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function MapPage() {
  const params = useParams();
  const router = useRouter();
  const mapId = params?.mapId as string;

  const map = getMapById(mapId);

  // If map not found or not active, show message
  if (!map) {
    return <div className="p-6">Map not found</div>;
  }

  if (map.status !== "active") {
    return (
      <div className="p-6">
        <Card>
          <CardHeader>
            <CardTitle>Map Unavailable</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">This map is not active and cannot be viewed.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex h-full gap-4">
      {/* Left sidebar: Layer list & metadata */}
      <aside className="w-72 border-r bg-card p-4">
        <h3 className="font-semibold mb-2">Layers & Metadata</h3>
        <div className="text-sm text-muted-foreground">Layer list and metadata placeholder</div>
      </aside>

      {/* Main area: Map container placeholder */}
      <main className="flex-1 p-4">
        <div className="h-[600px] w-full rounded border bg-muted/30 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-xl font-semibold">Map Canvas Placeholder</h2>
            <p className="text-sm text-muted-foreground">No map logic implemented yet. Map ID: {mapId}</p>
          </div>
        </div>
      </main>

      {/* Right panel: AI Chat interface */}
      <aside className="w-80 border-l bg-card p-4">
        <h3 className="font-semibold mb-2">AI Assistant</h3>
        <div className="text-sm text-muted-foreground">Chat interface placeholder</div>
      </aside>
    </div>
  );
}
