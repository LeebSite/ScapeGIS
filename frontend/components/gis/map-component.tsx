"use client";

import { useEffect, useRef, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ZoomIn, ZoomOut, Layers, Navigation } from "lucide-react";

export function MapComponent() {
  const mapRef = useRef<HTMLDivElement>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Simulate map loading
    const timer = setTimeout(() => setIsLoaded(true), 500);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="relative w-full h-full rounded-lg overflow-hidden border bg-muted">
      {/* Map Container */}
      <div
        ref={mapRef}
        className="w-full h-full bg-gradient-to-br from-blue-50 to-green-50 relative"
      >
        {/* Grid Pattern Overlay */}
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: `
              linear-gradient(to right, #000 1px, transparent 1px),
              linear-gradient(to bottom, #000 1px, transparent 1px)
            `,
            backgroundSize: "50px 50px",
          }}
        />

        {/* Sample Map Features */}
        <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-primary/20 rounded-full border-2 border-primary" />
        <div className="absolute top-1/2 right-1/4 w-24 h-24 bg-green-500/20 rounded-full border-2 border-green-500" />
        <div className="absolute bottom-1/4 left-1/3 w-40 h-40 bg-blue-500/20 rounded-full border-2 border-blue-500" />

        {/* Center Marker */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
          <div className="w-4 h-4 bg-red-500 rounded-full border-2 border-white shadow-lg" />
        </div>

        {/* Loading State */}
        {!isLoaded && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">Loading map...</p>
            </div>
          </div>
        )}
      </div>

      {/* Map Controls */}
      <div className="absolute bottom-4 right-4 flex flex-col space-y-2">
        <Button size="icon" variant="secondary" className="shadow-lg">
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button size="icon" variant="secondary" className="shadow-lg">
          <ZoomOut className="h-4 w-4" />
        </Button>
        <Button size="icon" variant="secondary" className="shadow-lg">
          <Navigation className="h-4 w-4" />
        </Button>
        <Button size="icon" variant="secondary" className="shadow-lg">
          <Layers className="h-4 w-4" />
        </Button>
      </div>

      {/* Map Info Overlay */}
      <Card className="absolute top-4 left-4 p-3 shadow-lg">
        <div className="text-sm">
          <p className="font-semibold">Map View</p>
          <p className="text-xs text-muted-foreground">Zoom: 12 | Coordinates: 40.7128°N, 74.0060°W</p>
        </div>
      </Card>
    </div>
  );
}

