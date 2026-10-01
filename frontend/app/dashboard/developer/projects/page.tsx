"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
    Plus, Map, Building2, MapPin, MoreVertical, Trash2,
    Archive, FolderKanban, Layers, Pencil,
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
import type { Project, ProjectType } from "@/lib/types";

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

// ---------- Create Project Modal ----------
function CreateProjectModal({
    open, onClose, onCreated, workspaceId,
}: {
    open: boolean; onClose: () => void; onCreated: () => void; workspaceId: string;
}) {
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [projectType, setProjectType] = useState<string>("other");
    const [city, setCity] = useState("");
    const [province, setProvince] = useState("");
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
            });
            toast.success("Project created!");
            onCreated();
            onClose();
            router.push(`/dashboard/developer/projects/${res.data.id}`);
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Failed to create project");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent className="sm:max-w-lg">
                <DialogHeader>
                    <DialogTitle>Create New Project</DialogTitle>
                    <DialogDescription>
                        Buat proyek analisis GIS baru di workspace Anda.
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-2">
                    <div className="grid gap-1.5">
                        <Label htmlFor="proj-name">Project Name *</Label>
                        <Input id="proj-name" placeholder="e.g. Analisis Lahan Jakarta Selatan"
                            value={name} onChange={(e) => setName(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleCreate()} />
                    </div>
                    <div className="grid gap-1.5">
                        <Label htmlFor="proj-desc">Description</Label>
                        <Textarea id="proj-desc" placeholder="Deskripsi proyek..."
                            rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="grid gap-1.5">
                            <Label>Project Type</Label>
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
                            <Label htmlFor="proj-city">City</Label>
                            <Input id="proj-city" placeholder="Jakarta Selatan"
                                value={city} onChange={(e) => setCity(e.target.value)} />
                        </div>
                    </div>
                    <div className="grid gap-1.5">
                        <Label htmlFor="proj-prov">Province</Label>
                        <Input id="proj-prov" placeholder="DKI Jakarta"
                            value={province} onChange={(e) => setProvince(e.target.value)} />
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={onClose} disabled={loading}>Cancel</Button>
                    <Button onClick={handleCreate} disabled={loading || !name.trim()}>
                        {loading ? "Creating..." : "Create Project"}
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
            toast.success("Project archived");
            onRefresh();
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Failed to archive");
        }
    };

    const handleDelete = async () => {
        if (!confirm(`Delete project "${project.name}"? This cannot be undone.`)) return;
        try {
            await projectAPI.deleteProject(project.id);
            toast.success("Project deleted");
            onRefresh();
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Failed to delete");
        }
    };

    return (
        <Card
            className="cursor-pointer hover:shadow-lg transition-shadow group"
            onClick={() => router.push(`/dashboard/developer/projects/${project.id}`)}
        >
            <CardContent className="p-0">
                {/* Map Preview Placeholder */}
                <div className="relative h-36 bg-muted overflow-hidden">
                    <div className="absolute inset-0"
                        style={{
                            backgroundImage: "radial-gradient(circle, hsl(var(--muted-foreground) / 0.08) 1px, transparent 1px)",
                            backgroundSize: "20px 20px",
                        }}
                    />
                    <div className="absolute inset-0 flex items-center justify-center text-muted-foreground/30 group-hover:text-muted-foreground/50 transition-colors">
                        <Map className="h-10 w-10" />
                    </div>
                    {/* Status badge */}
                    <div className="absolute top-2 left-2">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[project.status] || ""}`}>
                            {project.status}
                        </span>
                    </div>
                    {/* Actions */}
                    {isOwner && (
                        <div className="absolute top-2 right-2" onClick={(e) => e.stopPropagation()}>
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button variant="ghost" size="icon" className="h-7 w-7 bg-background/80 hover:bg-background">
                                        <MoreVertical className="h-4 w-4" />
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                    <DropdownMenuItem onClick={() => router.push(`/dashboard/developer/projects/${project.id}`)}>
                                        <Pencil className="mr-2 h-4 w-4" /> Edit
                                    </DropdownMenuItem>
                                    {project.status !== "archived" && (
                                        <DropdownMenuItem onClick={handleArchive}>
                                            <Archive className="mr-2 h-4 w-4" /> Archive
                                        </DropdownMenuItem>
                                    )}
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem className="text-destructive" onClick={handleDelete}>
                                        <Trash2 className="mr-2 h-4 w-4" /> Delete
                                    </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        </div>
                    )}
                </div>
                {/* Info */}
                <div className="p-4 space-y-2">
                    <h3 className="font-semibold text-base leading-tight truncate">{project.name}</h3>
                    <p className="text-sm text-muted-foreground line-clamp-1">
                        {project.description || "No description"}
                    </p>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground pt-1">
                        <Badge variant="outline" className="text-xs">
                            {PROJECT_TYPE_LABELS[project.project_type] || project.project_type}
                        </Badge>
                        {project.city && (
                            <span className="flex items-center gap-0.5">
                                <MapPin className="h-3 w-3" /> {project.city}
                            </span>
                        )}
                        <span className="flex items-center gap-0.5">
                            <Layers className="h-3 w-3" /> {project.layer_count} layers
                        </span>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

// ---------- Main Page ----------
export default function ProjectsPage() {
    const { currentWorkspace } = useWorkspaceStore();
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showCreate, setShowCreate] = useState(false);

    const isOwner = currentWorkspace?.role === "owner";

    const fetchProjects = useCallback(async () => {
        if (!currentWorkspace?.id) return;
        setLoading(true);
        setError(null);
        try {
            const res = await projectAPI.getProjects(currentWorkspace.id);
            setProjects(res.data.items);
        } catch (err: any) {
            setError(err?.response?.data?.detail || "Failed to load projects");
        } finally {
            setLoading(false);
        }
    }, [currentWorkspace?.id]);

    useEffect(() => {
        if (currentWorkspace?.id) {
            fetchProjects();
        } else {
            setLoading(false);
        }
    }, [currentWorkspace?.id, fetchProjects]);

    if (!currentWorkspace) {
        return (
            <div className="flex flex-col items-center justify-center py-20 text-center">
                <Building2 className="h-12 w-12 text-muted-foreground/50 mb-4" />
                <h3 className="font-semibold text-lg">No Workspace Selected</h3>
                <p className="text-muted-foreground text-sm mt-1">
                    Pilih workspace terlebih dahulu untuk melihat proyek.
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Projects</h1>
                    <p className="text-muted-foreground text-sm mt-1">
                        Kelola proyek GIS di <span className="font-medium">{currentWorkspace.name}</span>
                    </p>
                </div>
                {isOwner && (
                    <Button onClick={() => setShowCreate(true)} id="btn-create-project">
                        <Plus className="mr-2 h-4 w-4" /> New Project
                    </Button>
                )}
            </div>

            {/* Content */}
            {loading ? (
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {[1, 2, 3].map((i) => (
                        <Card key={i}>
                            <CardContent className="p-0">
                                <Skeleton className="h-36 w-full rounded-b-none" />
                                <div className="p-4 space-y-2">
                                    <Skeleton className="h-4 w-48" />
                                    <Skeleton className="h-3 w-32" />
                                    <Skeleton className="h-3 w-24" />
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            ) : error ? (
                <Card className="border-destructive/50">
                    <CardContent className="pt-6 text-center">
                        <p className="text-destructive text-sm">{error}</p>
                        <Button variant="outline" size="sm" className="mt-3" onClick={fetchProjects}>Retry</Button>
                    </CardContent>
                </Card>
            ) : projects.length === 0 ? (
                <Card className="border-dashed">
                    <CardContent className="pt-10 pb-10 flex flex-col items-center gap-4 text-center">
                        <div className="h-14 w-14 rounded-full bg-muted flex items-center justify-center">
                            <FolderKanban className="h-7 w-7 text-muted-foreground" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-lg">No Projects Yet</h3>
                            <p className="text-muted-foreground text-sm mt-1 max-w-sm">
                                Create your first project to start your GIS analysis.
                            </p>
                        </div>
                        {isOwner && (
                            <Button onClick={() => setShowCreate(true)}>
                                <Plus className="mr-2 h-4 w-4" /> Create Your First Project
                            </Button>
                        )}
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {projects.map((p) => (
                        <ProjectCard key={p.id} project={p} isOwner={isOwner} onRefresh={fetchProjects} />
                    ))}
                </div>
            )}

            {/* Create Modal */}
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
