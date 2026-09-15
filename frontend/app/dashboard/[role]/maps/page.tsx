"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { MapComponent } from "@/components/gis/map-component";
import { Plus, Layers, Search } from "lucide-react";

export default function MapsPage() {
  const [selectedMap, setSelectedMap] = useState<string | null>(null);

  const maps = [
    { id: "1", name: "Downtown Development", description: "Urban planning project", updated: "2 days ago" },
    { id: "2", name: "Residential Complex", description: "Housing development", updated: "1 week ago" },
    { id: "3", name: "Commercial Zone", description: "Business district analysis", updated: "3 days ago" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Maps</h2>
          <p className="text-muted-foreground">
            Manage and view your GIS maps
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          New Map
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>My Maps</CardTitle>
              <CardDescription>Select a map to view</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {maps.map((map) => (
                  <div
                    key={map.id}
                    onClick={() => setSelectedMap(map.id)}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                      selectedMap === map.id
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-accent"
                    }`}
                  >
                    <div className="flex items-center space-x-2 mb-1">
                      <Layers className="h-4 w-4" />
                      <h3 className="font-semibold">{map.name}</h3>
                    </div>
                    <p className={`text-sm ${selectedMap === map.id ? "text-primary-foreground/80" : "text-muted-foreground"}`}>
                      {map.description}
                    </p>
                    <p className={`text-xs mt-1 ${selectedMap === map.id ? "text-primary-foreground/60" : "text-muted-foreground"}`}>
                      Updated {map.updated}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-2">
          <Card className="h-[600px]">
            <CardHeader>
              <CardTitle>Map View</CardTitle>
              <CardDescription>
                {selectedMap
                  ? `Viewing: ${maps.find((m) => m.id === selectedMap)?.name}`
                  : "Select a map to view"}
              </CardDescription>
            </CardHeader>
            <CardContent className="h-[calc(100%-120px)]">
              {selectedMap ? (
                <MapComponent />
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  <div className="text-center">
                    <Layers className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Select a map from the list to view</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

