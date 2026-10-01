"use client";

import React from "react";
import { Check, ChevronsUpDown, PlusCircle, Building2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
    CommandSeparator,
} from "@/components/ui/command";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useWorkspaceStore } from "@/lib/store";
import { workspaceAPI } from "@/lib/api/WorkspaceService";
import type { Workspace } from "@/lib/types";
import { toast } from "sonner";

export function WorkspaceSelector() {
    const [open, setOpen] = React.useState(false);
    const [showNewWorkspaceDialog, setShowNewWorkspaceDialog] = React.useState(false);
    const { workspaces, currentWorkspace, setWorkspaces, setCurrentWorkspace } = useWorkspaceStore();
    const [newWorkspaceName, setNewWorkspaceName] = React.useState("");
    const [newWorkspaceDesc, setNewWorkspaceDesc] = React.useState("");
    const [isLoading, setIsLoading] = React.useState(false);
    const [isFetching, setIsFetching] = React.useState(false);

    // Fetch workspaces on mount
    const fetchWorkspaces = React.useCallback(async () => {
        setIsFetching(true);
        try {
            const res = await workspaceAPI.getWorkspaces();
            const list: Workspace[] = res.data || [];
            setWorkspaces(list);

            if (list.length > 0) {
                const storedId = typeof window !== "undefined" ? localStorage.getItem("current_workspace_id") : null;
                const found = list.find((w) => w.id === storedId);
                const active = found || list[0];
                setCurrentWorkspace(active);
            }
        } catch (error: any) {
            console.error("Failed to fetch workspaces:", error);
        } finally {
            setIsFetching(false);
        }
    }, [setWorkspaces, setCurrentWorkspace]);

    React.useEffect(() => {
        fetchWorkspaces();
    }, [fetchWorkspaces]);

    const handleCreateWorkspace = async () => {
        if (!newWorkspaceName.trim()) return;
        setIsLoading(true);
        try {
            const res = await workspaceAPI.createWorkspace({
                name: newWorkspaceName.trim(),
                description: newWorkspaceDesc.trim() || undefined,
            });
            const createdWorkspace: Workspace = res.data;
            toast.success(`Workspace "${createdWorkspace.name}" berhasil dibuat!`);
            
            // Refresh list & select newly created workspace
            const updatedList = [...workspaces, createdWorkspace];
            setWorkspaces(updatedList);
            setCurrentWorkspace(createdWorkspace);
            
            setShowNewWorkspaceDialog(false);
            setNewWorkspaceName("");
            setNewWorkspaceDesc("");
        } catch (error: any) {
            toast.error(error?.response?.data?.detail || "Gagal membuat workspace");
            console.error("Failed to create workspace:", error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Dialog open={showNewWorkspaceDialog} onOpenChange={setShowNewWorkspaceDialog}>
            <Popover open={open} onOpenChange={setOpen}>
                <PopoverTrigger asChild>
                    <Button
                        variant="outline"
                        role="combobox"
                        aria-expanded={open}
                        className="w-[210px] justify-between h-9 text-xs md:text-sm bg-background border-border/80 shadow-sm hover:bg-muted/50"
                    >
                        {currentWorkspace ? (
                            <div className="flex items-center gap-2 truncate">
                                <Building2 className="h-4 w-4 text-primary shrink-0" />
                                <span className="truncate font-medium">{currentWorkspace.name}</span>
                            </div>
                        ) : (
                            <span className="text-muted-foreground">
                                {isFetching ? "Memuat..." : "Pilih Workspace..."}
                            </span>
                        )}
                        <ChevronsUpDown className="ml-1 h-3.5 w-3.5 shrink-0 opacity-50" />
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-[220px] p-0" align="start">
                    <Command>
                        <CommandInput placeholder="Cari workspace..." />
                        <CommandList>
                            <CommandEmpty>Workspace tidak ditemukan.</CommandEmpty>
                            <CommandGroup heading="Daftar Workspace">
                                {workspaces.map((workspace) => (
                                    <CommandItem
                                        key={workspace.id}
                                        onSelect={() => {
                                            setCurrentWorkspace(workspace);
                                            setOpen(false);
                                            toast.info(`Berpindah ke workspace "${workspace.name}"`);
                                        }}
                                        className="text-xs md:text-sm cursor-pointer"
                                    >
                                        <Check
                                            className={cn(
                                                "mr-2 h-4 w-4 text-primary",
                                                currentWorkspace?.id === workspace.id
                                                    ? "opacity-100"
                                                    : "opacity-0"
                                            )}
                                        />
                                        <span className="truncate">{workspace.name}</span>
                                    </CommandItem>
                                ))}
                            </CommandGroup>
                        </CommandList>
                        <CommandSeparator />
                        <CommandList>
                            <CommandGroup>
                                <CommandItem
                                    onSelect={() => {
                                        setOpen(false);
                                        setShowNewWorkspaceDialog(true);
                                    }}
                                    className="cursor-pointer text-primary font-medium text-xs md:text-sm"
                                >
                                    <PlusCircle className="mr-2 h-4 w-4 text-primary" />
                                    + Workspace Baru
                                </CommandItem>
                            </CommandGroup>
                        </CommandList>
                    </Command>
                </PopoverContent>
            </Popover>

            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Building2 className="h-5 w-5 text-primary" />
                        Buat Workspace Baru
                    </DialogTitle>
                    <DialogDescription className="text-xs md:text-sm">
                        Workspace adalah wadah organisasi untuk mengelompokkan proyek GIS, dataset, dan anggota tim Anda.
                    </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-2">
                    <div className="space-y-1.5">
                        <Label htmlFor="ws-name-selector">Nama Workspace *</Label>
                        <Input
                            id="ws-name-selector"
                            placeholder="Contoh: PT Summarecon Land"
                            value={newWorkspaceName}
                            onChange={(e) => setNewWorkspaceName(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && handleCreateWorkspace()}
                        />
                    </div>
                    <div className="space-y-1.5">
                        <Label htmlFor="ws-desc-selector">Deskripsi (Opsional)</Label>
                        <Textarea
                            id="ws-desc-selector"
                            placeholder="Deskripsi tim atau fokus area pengawasan..."
                            rows={3}
                            value={newWorkspaceDesc}
                            onChange={(e) => setNewWorkspaceDesc(e.target.value)}
                        />
                    </div>
                </div>
                <DialogFooter className="gap-2 sm:gap-0">
                    <Button variant="outline" onClick={() => setShowNewWorkspaceDialog(false)} disabled={isLoading}>
                        Batal
                    </Button>
                    <Button onClick={handleCreateWorkspace} disabled={isLoading || !newWorkspaceName.trim()}>
                        {isLoading ? "Membuat..." : "Buat Workspace"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}