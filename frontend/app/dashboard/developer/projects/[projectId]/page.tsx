"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import {
    ArrowLeft, Layers, Plus, Eye, EyeOff, Trash2,
    Map as MapIcon, MapPin, Building2, Loader2, Settings2,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Slider } from "@/components/ui/slider";
import {
    Dialog, DialogContent, DialogHeader, DialogTitle,
    DialogDescription, DialogFooter,
} from "@/components/ui/dialog";
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { projectAPI } from "@/lib/api";
import { GISService } from "@/lib/api/GISService";
import { useWorkspaceStore } from "@/lib/store";
import type { ProjectDetail, ProjectLayer, ProjectType } from "@/lib/types";
import type { GISDataset, GISLayer as GISLayerType, GeoJSONFeatureCollection } from "@/lib/types/gis";

// Dynamically import MapLibre to avoid SSR issues
const MapboxMap = dynamic(() => import("@/components/gis/mapbox-map"), { ssr: false });

const PROJECT_TYPE_LABELS: Record<ProjectType, string> = {
    residential: "Residential",
    commercial: "Commercial",
    industrial: "Industrial",
    mixed_use: "Mixed Use",
    other: "Other",
};

const STATUS_COLORS: Record<string, string> = {
    draft: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
    active: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    archived: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
};

// ---------- Add Layer Modal ----------
function AddLayerModal({
    open, projectId, onClose, onAdded,
}: {
    open: boolean; projectId: string; onClose: () => void; onAdded: () => void;
}) {
    const [datasets, setDatasets] = useState<GISDataset[]>([]);
    const [selectedDataset, setSelectedDataset] = useState<string>("");
    const [layers, setLayers] = useState<GISLayerType[]>([]);
    const [selectedLayer, setSelectedLayer] = useState<string>("");
    const [loading, setLoading] = useState(false);
    const [loadingDatasets, setLoadingDatasets] = useState(false);

    useEffect(() => {
        if (open) {
            setLoadingDatasets(true);
            GISService.getDatasets().then((d) => {
                setDatasets(d.filter((ds) => ds.status === "completed"));
            }).catch(() => toast.error("Failed to load datasets"))
              .finally(() => setLoadingDatasets(false));
        }
    }, [open]);

    useEffect(() => {
        if (selectedDataset) {
            GISService.getDatasetLayers(selectedDataset).then(setLayers).catch(() => {});
            setSelectedLayer("");
        } else {
            setLayers([]);
        }
    }, [selectedDataset]);

    const handleAdd = async () => {
        if (!selectedDataset || !selectedLayer) return;
        setLoading(true);
        try {
            await projectAPI.addProjectLayer(projectId, {
                dataset_id: selectedDataset,
                layer_id: selectedLayer,
            });
            toast.success("Layer added!");
            onAdded();
            onClose();
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Failed to add layer");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Add GIS Layer</DialogTitle>
                    <DialogDescription>
                        Pilih dataset dan layer yang ingin ditambahkan ke proyek.
                    </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-2">
                    <div className="space-y-1.5">
                        <Label>Dataset</Label>
                        {loadingDatasets ? (
                            <Skeleton className="h-9 w-full" />
                        ) : (
                            <Select value={selectedDataset} onValueChange={setSelectedDataset}>
                                <SelectTrigger><SelectValue placeholder="Select dataset..." /></SelectTrigger>
                                <SelectContent>
                                    {datasets.map((ds) => (
                                        <SelectItem key={ds.id} value={ds.id}>
                                            {ds.name} ({ds.total_layers} layers)
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        )}
                    </div>
                    {selectedDataset && (
                        <div className="space-y-1.5">
                            <Label>Layer</Label>
                            <Select value={selectedLayer} onValueChange={setSelectedLayer}>
                                <SelectTrigger><SelectValue placeholder="Select layer..." /></SelectTrigger>
                                <SelectContent>
                                    {layers.map((l) => (
                                        <SelectItem key={l.id} value={l.id}>
                                            {l.name} ({l.geometry_type || "?"})
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    )}
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>Cancel</Button>
                    <Button onClick={handleAdd} disabled={loading || !selectedLayer}>
                        {loading ? "Adding..." : "Add Layer"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

// ---------- Layer Panel Item ----------
function LayerPanelItem({
    pl, isOwner, projectId, onRefresh,
}: {
    pl: ProjectLayer; isOwner: boolean; projectId: string; onRefresh: () => void;
}) {
    const [updating, setUpdating] = useState(false);

    const toggleVisibility = async () => {
        setUpdating(true);
        try {
            await projectAPI.updateProjectLayer(projectId, pl.id, { is_visible: !pl.is_visible });
            onRefresh();
        } catch { toast.error("Failed to update"); }
        finally { setUpdating(false); }
    };

    const updateOpacity = async (value: number[]) => {
        try {
            await projectAPI.updateProjectLayer(projectId, pl.id, { opacity: value[0] });
            onRefresh();
        } catch { toast.error("Failed to update"); }
    };

    const handleRemove = async () => {
        if (!confirm(`Remove layer "${pl.name}" from project?`)) return;
        try {
            await projectAPI.removeProjectLayer(projectId, pl.id);
            toast.success("Layer removed");
            onRefresh();
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Failed to remove");
        }
    };

    const geomIcon = (type?: string) => {
        if (!type) return "?";
        if (type.includes("Polygon")) return "◼";
        if (type.includes("Line")) return "—";
        if (type.includes("Point")) return "●";
        return "◆";
    };

    return (
        <div className="flex items-start gap-3 p-3 rounded-lg border bg-card hover:bg-accent/30 transition-colors">
            <button
                onClick={toggleVisibility}
                disabled={!isOwner || updating}
                className="mt-0.5 shrink-0 text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
            >
                {pl.is_visible ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
            </button>
            <div className="flex-1 min-w-0 space-y-1.5">
                <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">{geomIcon(pl.geometry_type)}</span>
                    <span className="text-sm font-medium truncate">{pl.name || "Unnamed"}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>{pl.geometry_type || "Unknown"}</span>
                    <span>·</span>
                    <span>{pl.feature_count} features</span>
                </div>
                {isOwner && (
                    <div className="flex items-center gap-2 pt-1">
                        <span className="text-xs text-muted-foreground w-12">Opacity</span>
                        <Slider
                            value={[pl.opacity]}
                            min={0} max={1} step={0.1}
                            onValueCommit={updateOpacity}
                            className="flex-1"
                        />
                        <span className="text-xs text-muted-foreground w-8 text-right">
                            {Math.round(pl.opacity * 100)}%
                        </span>
                    </div>
                )}
            </div>
            {isOwner && (
                <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0 text-muted-foreground hover:text-destructive"
                    onClick={handleRemove}>
                    <Trash2 className="h-3.5 w-3.5" />
                </Button>
            )}
        </div>
    );
}

// ---------- Edit Project Modal ----------
function EditProjectModal({
    open, project, onClose, onUpdated,
}: {
    open: boolean; project: ProjectDetail; onClose: () => void; onUpdated: () => void;
}) {
    const [name, setName] = useState(project.name);
    const [description, setDescription] = useState(project.description || "");
    const [projectType, setProjectType] = useState(project.project_type);
    const [city, setCity] = useState(project.city || "");
    const [province, setProvince] = useState(project.province || "");
    const [projectStatus, setProjectStatus] = useState(project.status);
    const [loading, setLoading] = useState(false);

    const handleSave = async () => {
        setLoading(true);
        try {
            await projectAPI.updateProject(project.id, {
                name, description, project_type: projectType,
                city, province, status: projectStatus,
            });
            toast.success("Project updated!");
            onUpdated();
            onClose();
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Failed to update");
        } finally { setLoading(false); }
    };

    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent className="sm:max-w-lg">
                <DialogHeader>
                    <DialogTitle>Edit Project</DialogTitle>
                </DialogHeader>
                <div className="grid gap-3 py-2">
                    <div className="grid gap-1.5">
                        <Label>Name</Label>
                        <Input value={name} onChange={(e) => setName(e.target.value)} />
                    </div>
                    <div className="grid gap-1.5">
                        <Label>Description</Label>
                        <Textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <div className="grid gap-1.5">
                            <Label>Type</Label>
                            <Select value={projectType} onValueChange={(val) => setProjectType(val as any)}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    {Object.entries(PROJECT_TYPE_LABELS).map(([k, v]) => (
                                        <SelectItem key={k} value={k}>{v}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="grid gap-1.5">
                            <Label>Status</Label>
                            <Select value={projectStatus} onValueChange={(val) => setProjectStatus(val as any)}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="draft">Draft</SelectItem>
                                    <SelectItem value="active">Active</SelectItem>
                                    <SelectItem value="archived">Archived</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <div className="grid gap-1.5">
                            <Label>City</Label>
                            <Input value={city} onChange={(e) => setCity(e.target.value)} />
                        </div>
                        <div className="grid gap-1.5">
                            <Label>Province</Label>
                            <Input value={province} onChange={(e) => setProvince(e.target.value)} />
                        </div>
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>Cancel</Button>
                    <Button onClick={handleSave} disabled={loading || !name.trim()}>
                        {loading ? "Saving..." : "Save Changes"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

// ---------- Main Page ----------
export default function ProjectDetailPage() {
    const { projectId } = useParams<{ projectId: string }>();
    const router = useRouter();
    const { currentWorkspace } = useWorkspaceStore();

    const [project, setProject] = useState<ProjectDetail | null>(null);
    const [layers, setLayers] = useState<ProjectLayer[]>([]);
    const [geojson, setGeojson] = useState<GeoJSONFeatureCollection | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showAddLayer, setShowAddLayer] = useState(false);
    const [showEdit, setShowEdit] = useState(false);

    const isOwner = currentWorkspace?.role === "owner";

    const fetchProject = useCallback(async () => {
        try {
            const res = await projectAPI.getProject(projectId);
            setProject(res.data);
        } catch (err: any) {
            setError(err?.response?.data?.detail || "Failed to load project");
        }
    }, [projectId]);

    const fetchLayers = useCallback(async () => {
        try {
            const res = await projectAPI.getProjectLayers(projectId);
            setLayers(res.data);
        } catch {
            console.error("Failed to load layers");
        }
    }, [projectId]);

    // Load GeoJSON for visible layers
    const loadGeoJSON = useCallback(async (projectLayers: ProjectLayer[]) => {
        const visibleLayers = projectLayers.filter((l) => l.is_visible);
        if (visibleLayers.length === 0) {
            setGeojson(null);
            return;
        }

        const allFeatures: any[] = [];
        for (const pl of visibleLayers) {
            try {
                const fc = await GISService.getLayerGeoJSON(pl.layer_id);
                if (fc?.features) {
                    // Apply opacity as property for potential styling
                    fc.features.forEach((f: any) => {
                        f.properties = { ...f.properties, _opacity: pl.opacity, _layer_name: pl.name };
                    });
                    allFeatures.push(...fc.features);
                }
            } catch {
                console.warn(`Failed to load GeoJSON for layer ${pl.layer_id}`);
            }
        }
        setGeojson({ type: "FeatureCollection", features: allFeatures });
    }, []);

    useEffect(() => {
        setLoading(true);
        Promise.all([fetchProject(), fetchLayers()]).finally(() => setLoading(false));
    }, [fetchProject, fetchLayers]);

    useEffect(() => {
        if (layers.length > 0) loadGeoJSON(layers);
    }, [layers, loadGeoJSON]);

    const handleLayerRefresh = () => {
        fetchLayers();
    };

    if (loading) {
        return (
            <div className="space-y-4">
                <Skeleton className="h-8 w-64" />
                <Skeleton className="h-[400px] w-full" />
            </div>
        );
    }

    if (error || !project) {
        return (
            <div className="flex flex-col items-center justify-center py-20">
                <p className="text-destructive mb-4">{error || "Project not found"}</p>
                <Button variant="outline" onClick={() => router.push("/dashboard/developer/projects")}>
                    <ArrowLeft className="mr-2 h-4 w-4" /> Back to Projects
                </Button>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                    <Button variant="ghost" size="icon" onClick={() => router.push("/dashboard/developer/projects")}>
                        <ArrowLeft className="h-5 w-5" />
                    </Button>
                    <div>
                        <div className="flex items-center gap-2">
                            <h1 className="text-2xl font-bold tracking-tight">{project.name}</h1>
                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[project.status] || ""}`}>
                                {project.status}
                            </span>
                        </div>
                        <div className="flex items-center gap-3 text-sm text-muted-foreground mt-1">
                            {project.workspace_name && (
                                <span className="flex items-center gap-1">
                                    <Building2 className="h-3.5 w-3.5" /> {project.workspace_name}
                                </span>
                            )}
                            <Badge variant="outline" className="text-xs">
                                {PROJECT_TYPE_LABELS[project.project_type] || project.project_type}
                            </Badge>
                            {project.city && (
                                <span className="flex items-center gap-1">
                                    <MapPin className="h-3.5 w-3.5" /> {project.city}{project.province ? `, ${project.province}` : ""}
                                </span>
                            )}
                        </div>
                    </div>
                </div>
                {isOwner && (
                    <Button variant="outline" size="sm" onClick={() => setShowEdit(true)}>
                        <Settings2 className="mr-2 h-4 w-4" /> Edit
                    </Button>
                )}
            </div>

            {project.description && (
                <p className="text-sm text-muted-foreground">{project.description}</p>
            )}

            {/* Map + Layer Panel */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                {/* Map */}
                <div className="lg:col-span-3">
                    <Card>
                        <CardContent className="p-0 overflow-hidden rounded-lg">
                            {layers.length === 0 ? (
                                <div className="flex flex-col items-center justify-center h-[500px] bg-muted/30 text-center">
                                    <MapIcon className="h-12 w-12 text-muted-foreground/30 mb-4" />
                                    <h3 className="font-semibold">No GIS Layers</h3>
                                    <p className="text-muted-foreground text-sm mt-1 max-w-sm">
                                        No GIS layers have been added to this project yet.
                                    </p>
                                    {isOwner && (
                                        <Button variant="outline" size="sm" className="mt-4" onClick={() => setShowAddLayer(true)}>
                                            <Plus className="mr-2 h-4 w-4" /> Add Layer
                                        </Button>
                                    )}
                                </div>
                            ) : (
                                <div style={{ height: "500px" }}>
                                    <MapboxMap geojson={geojson} />
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>

                {/* Layer Panel */}
                <div className="lg:col-span-1">
                    <Card className="h-full">
                        <CardHeader className="pb-3">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-sm font-medium flex items-center gap-2">
                                    <Layers className="h-4 w-4" /> Layers
                                </CardTitle>
                                {isOwner && (
                                    <Button variant="ghost" size="icon" className="h-7 w-7"
                                        onClick={() => setShowAddLayer(true)}>
                                        <Plus className="h-4 w-4" />
                                    </Button>
                                )}
                            </div>
                            <CardDescription className="text-xs">
                                {layers.length} layer{layers.length !== 1 ? "s" : ""} in project
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-2 max-h-[400px] overflow-y-auto">
                            {layers.length === 0 ? (
                                <p className="text-xs text-muted-foreground text-center py-4">
                                    No layers added yet.
                                </p>
                            ) : (
                                layers.map((pl) => (
                                    <LayerPanelItem
                                        key={pl.id}
                                        pl={pl}
                                        isOwner={isOwner}
                                        projectId={projectId}
                                        onRefresh={handleLayerRefresh}
                                    />
                                ))
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* Modals */}
            <AddLayerModal
                open={showAddLayer}
                projectId={projectId}
                onClose={() => setShowAddLayer(false)}
                onAdded={handleLayerRefresh}
            />
            {project && showEdit && (
                <EditProjectModal
                    open={showEdit}
                    project={project}
                    onClose={() => setShowEdit(false)}
                    onUpdated={() => { fetchProject(); }}
                />
            )}
        </div>
    );
}