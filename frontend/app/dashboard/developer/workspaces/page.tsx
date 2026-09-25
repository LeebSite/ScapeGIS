"use client";

import React, { useEffect, useState, useCallback } from "react";
import { Plus, Building2, Users, Crown, MoreVertical, Trash2, Pencil, Send } from "lucide-react";
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
import { useAuthStore } from "@/lib/store";
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
    onCreated: () => void;
}) {
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [loading, setLoading] = useState(false);

    const handleCreate = async () => {
        if (!name.trim()) return;
        setLoading(true);
        try {
            await workspaceAPI.createWorkspace({ name: name.trim(), description: description.trim() || undefined });
            toast.success("Workspace created!");
            setName("");
            setDescription("");
            onCreated();
            onClose();
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Failed to create workspace");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Create Workspace</DialogTitle>
                    <DialogDescription>
                        Workspace adalah organisasi Anda untuk mengelola proyek dan tim GIS.
                    </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-2">
                    <div className="space-y-1.5">
                        <Label htmlFor="ws-name">Workspace Name *</Label>
                        <Input
                            id="ws-name"
                            placeholder="e.g. PT Maju Property"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                        />
                    </div>
                    <div className="space-y-1.5">
                        <Label htmlFor="ws-desc">Description</Label>
                        <Textarea
                            id="ws-desc"
                            placeholder="Optional description..."
                            rows={3}
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                        />
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={onClose} disabled={loading}>Cancel</Button>
                    <Button onClick={handleCreate} disabled={loading || !name.trim()}>
                        {loading ? "Creating..." : "Create Workspace"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

// --------------------------------------------------------------------------
// INVITE MEMBER MODAL
// --------------------------------------------------------------------------
function InviteMemberModal({
    open,
    workspaceId,
    onClose,
}: {
    open: boolean;
    workspaceId: string;
    onClose: () => void;
}) {
    const [email, setEmail] = useState("");
    const [loading, setLoading] = useState(false);
    const [inviteToken, setInviteToken] = useState<string | null>(null);

    const handleInvite = async () => {
        if (!email.trim()) return;
        setLoading(true);
        try {
            const res = await workspaceAPI.inviteMember(workspaceId, { email: email.trim() });
            setInviteToken(res.data.token);
            toast.success("Invitation created!");
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Failed to send invitation");
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        setEmail("");
        setInviteToken(null);
        onClose();
    };

    const inviteLink = typeof window !== "undefined" && inviteToken
        ? `${window.location.origin}/invitations/${inviteToken}`
        : null;

    return (
        <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Invite Team Member</DialogTitle>
                    <DialogDescription>
                        Kirimkan undangan ke anggota tim Anda via email atau link.
                    </DialogDescription>
                </DialogHeader>
                {!inviteToken ? (
                    <div className="space-y-4 py-2">
                        <div className="space-y-1.5">
                            <Label htmlFor="invite-email">Email Address</Label>
                            <Input
                                id="invite-email"
                                type="email"
                                placeholder="member@company.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && handleInvite()}
                            />
                        </div>
                    </div>
                ) : (
                    <div className="space-y-3 py-2">
                        <p className="text-sm text-muted-foreground">
                            Invitation link berhasil dibuat. Bagikan link ini kepada <strong>{email}</strong>:
                        </p>
                        <div className="flex gap-2">
                            <Input readOnly value={inviteLink || ""} className="text-xs" />
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                    navigator.clipboard.writeText(inviteLink || "");
                                    toast.success("Copied!");
                                }}
                            >
                                Copy
                            </Button>
                        </div>
                        <p className="text-xs text-muted-foreground">Link berlaku selama 7 hari.</p>
                    </div>
                )}
                <DialogFooter>
                    <Button variant="outline" onClick={handleClose}>Close</Button>
                    {!inviteToken && (
                        <Button onClick={handleInvite} disabled={loading || !email.trim()}>
                            <Send className="mr-2 h-4 w-4" />
                            {loading ? "Sending..." : "Create Invite Link"}
                        </Button>
                    )}
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
    const [members, setMembers] = useState<WorkspaceMember[]>([]);
    const [expanded, setExpanded] = useState(false);
    const [loadingMembers, setLoadingMembers] = useState(false);
    const [showInvite, setShowInvite] = useState(false);
    const { user } = useAuthStore();

    const fetchMembers = useCallback(async () => {
        setLoadingMembers(true);
        try {
            const res = await workspaceAPI.getMembers(workspace.id);
            setMembers(res.data);
        } catch {
            toast.error("Failed to load members");
        } finally {
            setLoadingMembers(false);
        }
    }, [workspace.id]);

    useEffect(() => {
        if (expanded) fetchMembers();
    }, [expanded, fetchMembers]);

    const handleDelete = async () => {
        if (!confirm(`Delete workspace "${workspace.name}"? This cannot be undone.`)) return;
        try {
            await workspaceAPI.deleteWorkspace(workspace.id);
            toast.success("Workspace deleted");
            onDeleted();
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Failed to delete workspace");
        }
    };

    const isOwner = workspace.role === "owner";

    return (
        <>
            <Card className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                                <Building2 className="h-5 w-5 text-primary" />
                            </div>
                            <div>
                                <CardTitle className="text-base">{workspace.name}</CardTitle>
                                <CardDescription className="text-xs mt-0.5">/{workspace.slug}</CardDescription>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                            <Badge variant={isOwner ? "default" : "secondary"} className="text-xs">
                                {isOwner ? <Crown className="mr-1 h-3 w-3" /> : null}
                                {workspace.role}
                            </Badge>
                            {isOwner && (
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <Button variant="ghost" size="icon" className="h-7 w-7">
                                            <MoreVertical className="h-4 w-4" />
                                        </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="end">
                                        <DropdownMenuItem onClick={() => { setShowInvite(true); }}>
                                            <Send className="mr-2 h-4 w-4" /> Invite Member
                                        </DropdownMenuItem>
                                        <DropdownMenuSeparator />
                                        <DropdownMenuItem
                                            className="text-destructive focus:text-destructive"
                                            onClick={handleDelete}
                                        >
                                            <Trash2 className="mr-2 h-4 w-4" /> Delete Workspace
                                        </DropdownMenuItem>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            )}
                        </div>
                    </div>
                    {workspace.description && (
                        <p className="text-sm text-muted-foreground mt-2">{workspace.description}</p>
                    )}
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-between">
                        <button
                            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                            onClick={() => setExpanded(!expanded)}
                        >
                            <Users className="h-4 w-4" />
                            <span>{workspace.member_count} member{workspace.member_count !== 1 ? "s" : ""}</span>
                        </button>
                        <Button variant="ghost" size="sm" className="text-xs" onClick={() => setExpanded(!expanded)}>
                            {expanded ? "Hide" : "View Members"}
                        </Button>
                    </div>

                    {expanded && (
                        <>
                            <Separator className="my-3" />
                            {loadingMembers ? (
                                <div className="space-y-2">
                                    {[1, 2].map((i) => (
                                        <div key={i} className="flex items-center gap-3">
                                            <Skeleton className="h-8 w-8 rounded-full" />
                                            <div className="space-y-1">
                                                <Skeleton className="h-3 w-28" />
                                                <Skeleton className="h-3 w-40" />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {members.map((m) => (
                                        <div key={m.id} className="flex items-center gap-3">
                                            <Avatar className="h-8 w-8">
                                                <AvatarFallback className="text-xs">
                                                    {getInitials(m.user_name)}
                                                </AvatarFallback>
                                            </Avatar>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium truncate">{m.user_name || "Unknown"}</p>
                                                <p className="text-xs text-muted-foreground truncate">{m.user_email}</p>
                                            </div>
                                            <Badge variant={m.role === "owner" ? "default" : "outline"} className="text-xs shrink-0">
                                                {m.role}
                                            </Badge>
                                        </div>
                                    ))}
                                    {isOwner && (
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            className="w-full mt-2"
                                            onClick={() => setShowInvite(true)}
                                        >
                                            <Plus className="mr-2 h-4 w-4" /> Invite Member
                                        </Button>
                                    )}
                                </div>
                            )}
                        </>
                    )}
                </CardContent>
            </Card>

            <InviteMemberModal
                open={showInvite}
                workspaceId={workspace.id}
                onClose={() => setShowInvite(false)}
            />
        </>
    );
}

// --------------------------------------------------------------------------
// LOADING SKELETONS
// --------------------------------------------------------------------------
function WorkspaceSkeleton() {
    return (
        <Card>
            <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                    <Skeleton className="h-10 w-10 rounded-lg" />
                    <div className="space-y-2">
                        <Skeleton className="h-4 w-40" />
                        <Skeleton className="h-3 w-24" />
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <Skeleton className="h-4 w-32" />
            </CardContent>
        </Card>
    );
}

// --------------------------------------------------------------------------
// MAIN PAGE
// --------------------------------------------------------------------------
export default function WorkspacesPage() {
    const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showCreate, setShowCreate] = useState(false);

    const fetchWorkspaces = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await workspaceAPI.getWorkspaces();
            setWorkspaces(res.data);
        } catch (err: any) {
            setError(err?.response?.data?.detail || "Failed to load workspaces");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchWorkspaces();
    }, [fetchWorkspaces]);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Workspaces</h1>
                    <p className="text-muted-foreground text-sm mt-1">
                        Kelola organisasi dan tim Anda untuk proyek WebGIS.
                    </p>
                </div>
                <Button onClick={() => setShowCreate(true)} id="btn-create-workspace">
                    <Plus className="mr-2 h-4 w-4" />
                    New Workspace
                </Button>
            </div>

            {/* Content */}
            {loading ? (
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {[1, 2, 3].map((i) => <WorkspaceSkeleton key={i} />)}
                </div>
            ) : error ? (
                <Card className="border-destructive/50">
                    <CardContent className="pt-6 text-center">
                        <p className="text-destructive text-sm">{error}</p>
                        <Button variant="outline" size="sm" className="mt-3" onClick={fetchWorkspaces}>
                            Retry
                        </Button>
                    </CardContent>
                </Card>
            ) : workspaces.length === 0 ? (
                <Card className="border-dashed">
                    <CardContent className="pt-10 pb-10 flex flex-col items-center gap-4 text-center">
                        <div className="h-14 w-14 rounded-full bg-muted flex items-center justify-center">
                            <Building2 className="h-7 w-7 text-muted-foreground" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-lg">No Workspaces Yet</h3>
                            <p className="text-muted-foreground text-sm mt-1 max-w-sm">
                                Buat workspace pertama Anda untuk mulai mengelola proyek dan mengundang anggota tim.
                            </p>
                        </div>
                        <Button onClick={() => setShowCreate(true)}>
                            <Plus className="mr-2 h-4 w-4" /> Create Your First Workspace
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
                onCreated={fetchWorkspaces}
            />
        </div>
    );
}
