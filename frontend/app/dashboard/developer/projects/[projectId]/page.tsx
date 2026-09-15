"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { projectAPI } from "@/lib/api";
import type { Project, Layer } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { LayerSelector } from "@/components/layers/layer-selector";
import { Map, ArrowLeft, Trash2 } from "lucide-react";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";

export default function ProjectDetailPage({ params }: { params: { projectId: string } }) {
  const router = useRouter();
  const [project, setProject] = useState<Project | null>(null);
  const [layers, setLayers] = useState<Layer[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [projRes, layersRes] = await Promise.all([
        projectAPI.getProject(params.projectId),
        projectAPI.getProjectLayers(params.projectId),
      ]);
      setProject(projRes.data);
      setLayers(layersRes.data);
    } catch (error) {
      console.log(error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [params.projectId]);

  const handleAddLayer = async (layer: Layer) => {
    try {
      await projectAPI.assignLayer(params.projectId, layer.id);
      setLayers([...layers, layer]);
    } catch (error) {
      console.error("Failed to add layer", error);
    }
  };

  const handleRemoveLayer = async (layerId: string) => {
    try {
      await projectAPI.removeLayer(params.projectId, layerId);
      setLayers(layers.filter(l => l.id !== layerId));
    } catch (error) {
      console.error("Failed to remove layer", error);
    }
  };

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="border-b px-6 py-4 flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-xl font-semibold">{project?.name || "Loading..."}</h1>
          <p className="text-sm text-muted-foreground">{project?.description || `ID: ${params.projectId}`}</p>
        </div>
        <div className="ml-auto">
          <Button>
            <Map className="mr-2 h-4 w-4" />
            Open in Map Viewer
          </Button>
        </div>
      </div>

      <div className="flex-1 p-6 space-y-6">
        <div className="grid gap-6 md:grid-cols-3">
          <div className="md:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex justify-between items-center">
                  <span>Map Layers</span>
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button size="sm" variant="outline">Add Layer</Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[500px]">
                      <LayerSelector
                        onSelect={handleAddLayer}
                        selectedLayerIds={layers.map(l => l.id)}
                      />
                    </DialogContent>
                  </Dialog>
                </CardTitle>
                <CardDescription>Manage the layers visible in this project.</CardDescription>
              </CardHeader>
              <CardContent>
                {layers.length === 0 ? (
                  <div className="text-center py-8 text-black/50">No layers added yet.</div>
                ) : (
                  <div className="space-y-4">
                    {layers.map(layer => (
                      <div key={layer.id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <p className="font-medium">{layer.name}</p>
                          <p className="text-sm text-muted-foreground">{layer.type} • {layer.region}</p>
                        </div>
                        <Button variant="ghost" size="icon" onClick={() => handleRemoveLayer(layer.id)}>
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Mock Settings */}
                <div className="flex justify-between items-center">
                  <span className="text-sm">Public Access</span>
                  <Button variant="outline" size="sm">Disabled</Button>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Collaborators</span>
                  <Button variant="outline" size="sm">Manage</Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
