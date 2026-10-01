"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
    Plus, Map, Building2, MapPin, MoreVertical, Trash2,
    Archive, FolderKanban, Layers, Pencil, ArrowRight
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
    Dialog, DialogContent, DialogHeader, DialogTitle,
    DialogDescription, DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
    DropdownMenu, DropdownMenuContent, DropdownMenuItem,
    DropdownMenuTrigger, DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { useWorkspaceStore } from "@/lib/store";
import { projectAPI } from "@/lib/api";
import { workspaceAPI, type Workspace } from "@/lib/api/WorkspaceService";
import type { Project, ProjectType } from "@/lib/types";

const PROJECT_TYPE_LABELS: Record<ProjectType, string> = {
    residential: "Residential (Perumahan)",
    commercial: "Commercial (Komersial)",
    industrial: "Industrial (Kawasan Industri)",
    mixed_use: "Mixed Use (Campuran)",
    other: "Other (Lainnya)",
};

const STATUS_COLORS: Record<string, string> = {
    draft: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400 border-amber-200",
    active: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400 border-emerald-200",
    archived: "bg-muted text-muted-foreground border-border",
};

// ---------- Create Project Modal ----------
function CreateProjectModal({
    open, onClose, onCreated, workspaceId,
}: {
    open: boolean; onClose: () => void; onCreated: () => void; workspaceId: string;
}) {
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [projectType, setProjectType] = useState<string>("residential");
    const [city, setCity] = useState("Tangerang Selatan");
    const [province, setProvince] = useState("Banten");
    const [centerLat, setCenterLat] = useState<number>(-6.3000);
    const [centerLng, setCenterLng] = useState<number>(106.6500);
    const [zoom, setZoom] = useState<number>(13);
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const handleCreate = async () => {
        if (!name.trim()) return;
        setLoading(true);
        try {
            const res = await projectAPI.createProject({
                workspace_id: workspaceId,
                name: name.trim(),
                description: description.trim() || undefined,
                project_type: projectType,
                city: city.trim() || undefined,
                province: province.trim() || undefined,
                center_lat: centerLat,
                center_lng: centerLng,
                zoom: zoom,
            });
            toast.success(`Project "${res.data.name}" berhasil dibuat!`);
            onCreated();
            onClose();
            router.push(`/dashboard/developer/projects/${res.data.id}`);
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Gagal membuat proyek");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent className="sm:max-w-lg">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <FolderKanban className="h-5 w-5 text-primary" />
                        Buat Proyek GIS Baru
                    </DialogTitle>
                    <DialogDescription className="text-xs md:text-sm">
                        Proyek adalah ruang analisis geospasial untuk lokasi pembangunan properti Anda.
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-2 text-sm">
                    <div className="grid gap-1.5">
                        <Label htmlFor="proj-name">Nama Proyek *</Label>
                        <Input id="proj-name" placeholder="Contoh: Kawasan BSD City Cluster A"
                            value={name} onChange={(e) => setName(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleCreate()} />
                    </div>
                    <div className="grid gap-1.5">
                        <Label htmlFor="proj-desc">Deskripsi Proyek</Label>
                        <Textarea id="proj-desc" placeholder="Rencana pembangunan, estimasi luas lahan, dsb..."
                            rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="grid gap-1.5">
                            <Label>Tipe Proyek</Label>
                            <Select value={projectType} onValueChange={setProjectType}>
                                <SelectTrigger><SelectValue /></SelectTrigger>
                                <SelectContent>
                                    {Object.entries(PROJECT_TYPE_LABELS).map(([k, v]) => (
                                        <SelectItem key={k} value={k}>{v}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="grid gap-1.5">
                            <Label htmlFor="proj-city">Kota / Kabupaten</Label>
                            <Input id="proj-city" placeholder="Tangerang Selatan"
                                value={city} onChange={(e) => setCity(e.target.value)} />
                        </div>
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                        <div className="grid gap-1.5">
                            <Label htmlFor="proj-lat">Latitude</Label>
                            <Input id="proj-lat" type="number" step="0.0001" value={centerLat}
                                onChange={(e) => setCenterLat(parseFloat(e.target.value) || 0)} />
                        </div>
                        <div className="grid gap-1.5">
                            <Label htmlFor="proj-lng">Longitude</Label>
                            <Input id="proj-lng" type="number" step="0.0001" value={centerLng}
                                onChange={(e) => setCenterLng(parseFloat(e.target.value) || 0)} />
                        </div>
                        <div className="grid gap-1.5">
                            <Label htmlFor="proj-zoom">Zoom Level</Label>
                            <Input id="proj-zoom" type="number" min="1" max="20" value={zoom}
                                onChange={(e) => setZoom(parseInt(e.target.value) || 13)} />
                        </div>
                    </div>
                </div>
                <DialogFooter className="gap-2 sm:gap-0">
                    <Button variant="outline" onClick={onClose} disabled={loading}>Batal</Button>
                    <Button onClick={handleCreate} disabled={loading || !name.trim()}>
                        {loading ? "Membuat Proyek..." : "Buat Proyek"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

// ---------- Project Card ----------
function ProjectCard({ project, isOwner, onRefresh }: {
    project: Project; isOwner: boolean; onRefresh: () => void;
}) {
    const router = useRouter();

    const handleArchive = async () => {
        try {
            await projectAPI.archiveProject(project.id);
            toast.success("Proyek diarsipkan");
            onRefresh();
        } catch (err: any) {
            toast.error("Gagal mengarsipkan proyek");
        }
    };

    const handleDelete = async () => {
        if (!confirm(`Hapus proyek "${project.name}" secara permanen?`)) return;
        try {
            await projectAPI.deleteProject(project.id);
            toast.success("Proyek berhasil dihapus");
            onRefresh();
        } catch (err: any) {
            toast.error("Gagal menghapus proyek");
        }
    };

    return (
        <Card className="hover:border-primary/50 transition-all shadow-sm duration-200 group flex flex-col justify-between">
            <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                    <div className="space-y-1">
                        <div className="flex items-center gap-2">
                            <Badge variant="outline" className={`text-[10px] capitalize px-2 py-0.5 border ${STATUS_COLORS[project.status] || ""}`}>
                                {project.status}
                            </Badge>
                            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
                                {PROJECT_TYPE_LABELS[project.project_type as ProjectType] || project.project_type}
                            </span>
                        </div>
                        <CardTitle className="text-base font-semibold group-hover:text-primary transition-colors mt-1">
                            {project.name}
                        </CardTitle>
                    </div>
                    {isOwner && (
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0">
                                    <MoreVertical className="h-4 w-4" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={handleArchive}>
                                    <Archive className="mr-2 h-4 w-4" /> Arsipkan
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onClick={handleDelete} className="text-destructive">
                                    <Trash2 className="mr-2 h-4 w-4" /> Hapus Proyek
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    )}
                </div>
                <CardDescription className="text-xs line-clamp-2 mt-2">
                    {project.description || "Belum ada deskripsi proyek."}
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
                <div className="flex items-center justify-between text-xs text-muted-foreground border-t pt-2.5">
                    <div className="flex items-center gap-1.5">
                        <MapPin className="h-3.5 w-3.5 text-primary shrink-0" />
                        <span className="truncate">{project.city ? `${project.city}, ${project.province || ""}` : "Lokasi belum diset"}</span>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                        <Layers className="h-3.5 w-3.5 text-muted-foreground" />
                        <span>{project.layer_count || 0} Layer</span>
                    </div>
                </div>

                <Button
                    className="w-full text-xs font-medium"
                    onClick={() => router.push(`/dashboard/developer/projects/${project.id}`)}
                >
                    <Map className="mr-2 h-4 w-4" /> Buka Peta MapLibre GIS
                    <ArrowRight className="ml-auto h-3.5 w-3.5" />
                </Button>
            </CardContent>
        </Card>
    );
}

// ---------- Main Component ----------
export default function ProjectsPage() {
    const { currentWorkspace, setWorkspaces, setCurrentWorkspace } = useWorkspaceStore();
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showCreate, setShowCreate] = useState(false);
    const router = useRouter();

    // Ensure we have a current workspace loaded
    useEffect(() => {
        const initWorkspaces = async () => {
            if (!currentWorkspace) {
                try {
                    const res = await workspaceAPI.getWorkspaces();
                    const list = res.data || [];
                    setWorkspaces(list);
                    if (list.length > 0) {
                        const storedId = localStorage.getItem("current_workspace_id");
                        const found = list.find((w) => w.id === storedId);
                        setCurrentWorkspace(found || list[0]);
                    }
                } catch (err) {
                    console.error("Failed to load workspace list:", err);
                }
            }
        };
        initWorkspaces();
    }, [currentWorkspace, setCurrentWorkspace, setWorkspaces]);

    const fetchProjects = useCallback(async () => {
        if (!currentWorkspace?.id) {
            setLoading(false);
            return;
        }
        setLoading(true);
        setError(null);
        try {
            const res = await projectAPI.getProjects(currentWorkspace.id);
            setProjects(res.data.items || []);
        } catch (err: any) {
            setError(err?.response?.data?.detail || "Gagal memuat daftar proyek");
        } finally {
            setLoading(false);
        }
    }, [currentWorkspace?.id]);

    useEffect(() => {
        fetchProjects();
    }, [fetchProjects]);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Proyek GIS</h1>
                    <p className="text-muted-foreground text-sm mt-1">
                        {currentWorkspace
                            ? `Daftar proyek geospasial di workspace "${currentWorkspace.name}"`
                            : "Pilih workspace untuk mengelola proyek lokasi Anda."}
                    </p>
                </div>
                <Button
                    onClick={() => setShowCreate(true)}
                    disabled={!currentWorkspace}
                    className="sm:self-auto self-start"
                >
                    <Plus className="mr-2 h-4 w-4" />
                    + Project Baru
                </Button>
            </div>

            {/* If no workspace exists */}
            {!currentWorkspace && !loading ? (
                <Card className="border-dashed border-primary/40 bg-primary/5">
                    <CardContent className="pt-8 pb-8 flex flex-col items-center gap-4 text-center">
                        <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                            <Building2 className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-base">Belum Ada Workspace Terpilih</h3>
                            <p className="text-muted-foreground text-sm mt-1 max-w-sm">
                                Buat atau pilih workspace terlebih dahulu sebelum membuat proyek geospasial.
                            </p>
                        </div>
                        <Button onClick={() => router.push("/dashboard/developer/workspaces")}>
                            <Building2 className="mr-2 h-4 w-4" /> Kelola Workspace
                        </Button>
                    </CardContent>
                </Card>
            ) : loading ? (
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {[1, 2, 3].map((i) => (
                        <Card key={i} className="p-6 space-y-4">
                            <Skeleton className="h-5 w-1/3" />
                            <Skeleton className="h-6 w-2/3" />
                            <Skeleton className="h-16 w-full" />
                        </Card>
                    ))}
                </div>
            ) : error ? (
                <Card className="border-destructive/50">
                    <CardContent className="pt-6 text-center">
                        <p className="text-destructive text-sm">{error}</p>
                        <Button variant="outline" size="sm" className="mt-3" onClick={fetchProjects}>
                            Coba Lagi
                        </Button>
                    </CardContent>
                </Card>
            ) : projects.length === 0 ? (
                <Card className="border-dashed">
                    <CardContent className="pt-10 pb-10 flex flex-col items-center gap-4 text-center">
                        <div className="h-14 w-14 rounded-full bg-muted flex items-center justify-center">
                            <FolderKanban className="h-7 w-7 text-muted-foreground" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-lg">Belum Ada Proyek GIS</h3>
                            <p className="text-muted-foreground text-sm mt-1 max-w-sm">
                                Mulai analisis lahan Anda dengan membuat proyek geospasial pertama di workspace ini.
                            </p>
                        </div>
                        <Button onClick={() => setShowCreate(true)}>
                            <Plus className="mr-2 h-4 w-4" /> Buat Proyek Pertama Anda
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {projects.map((proj) => (
                        <ProjectCard
                            key={proj.id}
                            project={proj}
                            isOwner={currentWorkspace?.role === "owner"}
                            onRefresh={fetchProjects}
                        />
                    ))}
                </div>
            )}

            {/* Create Project Modal */}
            {currentWorkspace && (
                <CreateProjectModal
                    open={showCreate}
                    onClose={() => setShowCreate(false)}
                    onCreated={fetchProjects}
                    workspaceId={currentWorkspace.id}
                />
            )}
        </div>
    );
}