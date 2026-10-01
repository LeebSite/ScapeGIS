"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
    Plus, Building2, Users, Crown, MoreVertical, Trash2,
    Pencil, Send, FolderKanban, ArrowRight
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
    DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import { workspaceAPI, type Workspace, type WorkspaceMember } from "@/lib/api/WorkspaceService";
import { useAuthStore, useWorkspaceStore } from "@/lib/store";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

// --------------------------------------------------------------------------
// HELPER
// --------------------------------------------------------------------------
function getInitials(name?: string | null): string {
    if (!name) return "?";
    return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

// --------------------------------------------------------------------------
// CREATE WORKSPACE MODAL
// --------------------------------------------------------------------------
function CreateWorkspaceModal({
    open,
    onClose,
    onCreated,
}: {
    open: boolean;
    onClose: () => void;
    onCreated: (newWs: Workspace) => void;
}) {
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [loading, setLoading] = useState(false);

    const handleCreate = async () => {
        if (!name.trim()) return;
        setLoading(true);
        try {
            const res = await workspaceAPI.createWorkspace({ name: name.trim(), description: description.trim() || undefined });
            toast.success(`Workspace "${res.data.name}" berhasil dibuat!`);
            setName("");
            setDescription("");
            onCreated(res.data);
            onClose();
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Gagal membuat workspace");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Building2 className="h-5 w-5 text-primary" />
                        Buat Ruang Kerja (Workspace) Baru
                    </DialogTitle>
                    <DialogDescription className="text-xs md:text-sm">
                        Workspace adalah organisasi untuk mengelompokkan tim, proyek GIS, dan dataset lokasi Anda.
                    </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-2">
                    <div className="space-y-1.5">
                        <Label htmlFor="ws-name">Nama Workspace *</Label>
                        <Input
                            id="ws-name"
                            placeholder="Contoh: PT Summarecon Land"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                        />
                    </div>
                    <div className="space-y-1.5">
                        <Label htmlFor="ws-desc">Deskripsi (Opsional)</Label>
                        <Textarea
                            id="ws-desc"
                            placeholder="Deskripsi singkat mengenai divisi atau wilayah proyek..."
                            rows={3}
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                        />
                    </div>
                </div>
                <DialogFooter className="gap-2 sm:gap-0">
                    <Button variant="outline" onClick={onClose} disabled={loading}>Batal</Button>
                    <Button onClick={handleCreate} disabled={loading || !name.trim()}>
                        {loading ? "Membuat..." : "Buat Workspace"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

// --------------------------------------------------------------------------
// WORKSPACE CARD
// --------------------------------------------------------------------------
function WorkspaceCard({
    workspace,
    onDeleted,
    onRefresh,
}: {
    workspace: Workspace;
    onDeleted: () => void;
    onRefresh: () => void;
}) {
    const router = useRouter();
    const { user } = useAuthStore();
    const { currentWorkspace, setCurrentWorkspace } = useWorkspaceStore();
    const [expanded, setExpanded] = useState(false);
    const [members, setMembers] = useState<WorkspaceMember[]>([]);
    const [loadingMembers, setLoadingMembers] = useState(false);
    const [showInvite, setShowInvite] = useState(false);
    const [deleting, setDeleting] = useState(false);

    const isOwner = workspace.role === "owner" || workspace.owner_id === user?.id;
    const isSelected = currentWorkspace?.id === workspace.id;

    const handleOpenWorkspace = () => {
        setCurrentWorkspace(workspace);
        router.push("/dashboard/developer/projects");
    };

    const toggleMembers = async () => {
        if (!expanded && members.length === 0) {
            setLoadingMembers(true);
            try {
                const res = await workspaceAPI.getMembers(workspace.id);
                setMembers(res.data);
            } catch (err) {
                toast.error("Gagal memuat daftar anggota");
            } finally {
                setLoadingMembers(false);
            }
        }
        setExpanded(!expanded);
    };

    const handleDelete = async () => {
        if (!confirm(`Apakah Anda yakin ingin menghapus workspace "${workspace.name}"?`)) return;
        setDeleting(true);
        try {
            await workspaceAPI.deleteWorkspace(workspace.id);
            toast.success("Workspace berhasil dihapus");
            onDeleted();
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Gagal menghapus workspace");
        } finally {
            setDeleting(false);
        }
    };

    return (
        <Card className={`transition-all duration-200 border ${isSelected ? "border-primary shadow-md bg-primary/5" : "hover:border-primary/50 shadow-sm"}`}>
            <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                        <div className={`p-2.5 rounded-xl ${isSelected ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"}`}>
                            <Building2 className="h-5 w-5" />
                        </div>
                        <div>
                            <CardTitle className="text-base font-semibold flex items-center gap-2">
                                {workspace.name}
                                {isOwner && (
                                    <Crown className="h-3.5 w-3.5 text-amber-500"  />
                                )}
                            </CardTitle>
                            <CardDescription className="text-xs line-clamp-1 mt-0.5">
                                {workspace.description || "Tidak ada deskripsi"}
                            </CardDescription>
                        </div>
                    </div>
                    {isOwner && (
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                    <MoreVertical className="h-4 w-4" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={handleDelete} className="text-destructive">
                                    <Trash2 className="mr-2 h-4 w-4" /> Hapus Workspace
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    )}
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="flex items-center justify-between text-xs text-muted-foreground pt-1 border-t">
                    <div className="flex items-center gap-2">
                        <Badge variant={workspace.role === "owner" ? "default" : "secondary"} className="capitalize text-[10px]">
                            {workspace.role || "Member"}
                        </Badge>
                        <span></span>
                        <span>{workspace.member_count || 1} Anggota</span>
                    </div>
                </div>

                <div className="flex items-center gap-2 pt-1">
                    <Button
                        size="sm"
                        className="w-full text-xs font-medium"
                        variant={isSelected ? "default" : "outline"}
                        onClick={handleOpenWorkspace}
                    >
                        <FolderKanban className="mr-1.5 h-3.5 w-3.5" />
                        {isSelected ? "Buka Proyek Aktif" : "Pilih & Lihat Proyek"}
                        <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}

// --------------------------------------------------------------------------
// MAIN WORKSPACES PAGE
// --------------------------------------------------------------------------
export default function WorkspacesPage() {
    const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showCreate, setShowCreate] = useState(false);
    const { setWorkspaces: setStoreWorkspaces, setCurrentWorkspace } = useWorkspaceStore();

    const fetchWorkspaces = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await workspaceAPI.getWorkspaces();
            const list = res.data || [];
            setWorkspaces(list);
            setStoreWorkspaces(list);
        } catch (err: any) {
            setError(err?.response?.data?.detail || "Gagal memuat ruang kerja");
        } finally {
            setLoading(false);
        }
    }, [setStoreWorkspaces]);

    useEffect(() => {
        fetchWorkspaces();
    }, [fetchWorkspaces]);

    const handleCreated = (newWs: Workspace) => {
        const updated = [...workspaces, newWs];
        setWorkspaces(updated);
        setStoreWorkspaces(updated);
        setCurrentWorkspace(newWs);
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Ruang Kerja (Workspaces)</h1>
                    <p className="text-muted-foreground text-sm mt-1">
                        Kelola organisasi dan tim Anda untuk proyek analisis lokasi WebGIS & AI.
                    </p>
                </div>
                <Button onClick={() => setShowCreate(true)} className="sm:self-auto self-start">
                    <Plus className="mr-2 h-4 w-4" />
                    + Workspace Baru
                </Button>
            </div>

            {/* Content Grid */}
            {loading ? (
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {[1, 2, 3].map((i) => (
                        <Card key={i} className="p-6 space-y-4">
                            <Skeleton className="h-6 w-1/2" />
                            <Skeleton className="h-4 w-3/4" />
                            <Skeleton className="h-9 w-full" />
                        </Card>
                    ))}
                </div>
            ) : error ? (
                <Card className="border-destructive/50">
                    <CardContent className="pt-6 text-center">
                        <p className="text-destructive text-sm">{error}</p>
                        <Button variant="outline" size="sm" className="mt-3" onClick={fetchWorkspaces}>
                            Coba Lagi
                        </Button>
                    </CardContent>
                </Card>
            ) : workspaces.length === 0 ? (
                <Card className="border-dashed">
                    <CardContent className="pt-10 pb-10 flex flex-col items-center gap-4 text-center">
                        <div className="h-14 w-14 rounded-full bg-primary/10 flex items-center justify-center">
                            <Building2 className="h-7 w-7 text-primary" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-lg">Belum Ada Workspace</h3>
                            <p className="text-muted-foreground text-sm mt-1 max-w-sm">
                                Buat workspace pertama Anda untuk mulai mengelola proyek properti dan peta GIS.
                            </p>
                        </div>
                        <Button onClick={() => setShowCreate(true)}>
                            <Plus className="mr-2 h-4 w-4" /> Buat Workspace Pertama Anda
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {workspaces.map((ws) => (
                        <WorkspaceCard
                            key={ws.id}
                            workspace={ws}
                            onDeleted={fetchWorkspaces}
                            onRefresh={fetchWorkspaces}
                        />
                    ))}
                </div>
            )}

            {/* Create Modal */}
            <CreateWorkspaceModal
                open={showCreate}
                onClose={() => setShowCreate(false)}
                onCreated={handleCreated}
            />
        </div>
    );
}
