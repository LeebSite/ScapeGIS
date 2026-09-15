"use client";

import * as React from "react";
import { Check, ChevronsUpDown, PlusCircle } from "lucide-react";
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
    DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/lib/store";
import { workspaceAPI } from "@/lib/api";
import type { Workspace } from "@/lib/types";

export function WorkspaceSelector() {
    const [open, setOpen] = React.useState(false);
    const [showNewWorkspaceDialog, setShowNewWorkspaceDialog] = React.useState(false);
    const [workspaces, setWorkspaces] = React.useState<Workspace[]>([]);
    const [selectedWorkspace, setSelectedWorkspace] = React.useState<Workspace | null>(null);
    const [newWorkspaceName, setNewWorkspaceName] = React.useState("");
    const [isLoading, setIsLoading] = React.useState(false);
    const [error, setError] = React.useState<string | null>(null);

    // Fetch workspaces on mount
    React.useEffect(() => {
        const fetchWorkspaces = async () => {
            try {
                setError(null);
                const res = await workspaceAPI.getWorkspaces();
                setWorkspaces(res.data);
                if (res.data.length > 0) {
                    // Check if there's a stored workspace ID
                    const storedId = localStorage.getItem("current_workspace_id");
                    const found = res.data.find(w => w.id === storedId);
                    setSelectedWorkspace(found || res.data[0]);
                }
            } catch (error: any) {
                console.error("Failed to fetch workspaces:", error);
                // Check if it's a 404 error (endpoint not implemented)
                if (error?.response?.status === 404) {
                    setError("Workspace feature not available");
                } else {
                    setError("Failed to load workspaces");
                }
            }
        };
        fetchWorkspaces();
    }, []);

    // Update localStorage when selection changes
    React.useEffect(() => {
        if (selectedWorkspace) {
            localStorage.setItem("current_workspace_id", selectedWorkspace.id);
        }
    }, [selectedWorkspace]);

    const handleCreateWorkspace = async () => {
        setIsLoading(true);
        try {
            const res = await workspaceAPI.createWorkspace({ name: newWorkspaceName });
            setWorkspaces([...workspaces, res.data]);
            setSelectedWorkspace(res.data);
            setShowNewWorkspaceDialog(false);
            setNewWorkspaceName("");
        } catch (error) {
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
                        className="w-[200px] justify-between"
                        disabled={!!error}
                        title={error || undefined}
                    >
                        {error ? (
                            <span className="truncate text-muted-foreground">{error}</span>
                        ) : selectedWorkspace ? (
                            <div className="flex items-center gap-2 truncate">
                                <span className="truncate font-medium">{selectedWorkspace.name}</span>
                            </div>

                        ) : (
                            "Select workspace..."
                        )}
                        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-[200px] p-0">
                    <Command>
                        <CommandInput placeholder="Search workspace..." />
                        <CommandList>
                            <CommandEmpty>No workspace found.</CommandEmpty>
                            <CommandGroup heading="Workspaces">
                                {workspaces.map((workspace) => (
                                    <CommandItem
                                        key={workspace.id}
                                        onSelect={() => {
                                            setSelectedWorkspace(workspace);
                                            setOpen(false);
                                        }}
                                        className="text-sm"
                                    >
                                        <Check
                                            className={cn(
                                                "mr-2 h-4 w-4",
                                                selectedWorkspace?.id === workspace.id
                                                    ? "opacity-100"
                                                    : "opacity-0"
                                            )}
                                        />
                                        {workspace.name}
                                    </CommandItem>
                                ))}
                            </CommandGroup>
                        </CommandList>
                        <CommandSeparator />
                        <CommandList>
                            <CommandGroup>
                                <DialogTrigger asChild>
                                    <CommandItem
                                        onSelect={() => {
                                            setOpen(false);
                                            setShowNewWorkspaceDialog(true);
                                        }}
                                    >
                                        <PlusCircle className="mr-2 h-5 w-5" />
                                        Create Workspace
                                    </CommandItem>
                                </DialogTrigger>
                            </CommandGroup>
                        </CommandList>
                    </Command>
                </PopoverContent>
            </Popover>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Create Workspace</DialogTitle>
                    <DialogDescription>
                        Add a new workspace to manage products and customers.
                    </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-2 pb-4">
                    <div className="space-y-2">
                        <Label htmlFor="name">Workspace Name</Label>
                        <Input
                            id="name"
                            placeholder="Acme Inc."
                            value={newWorkspaceName}
                            onChange={(e) => setNewWorkspaceName(e.target.value)}
                        />
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={() => setShowNewWorkspaceDialog(false)}>
                        Cancel
                    </Button>
                    <Button type="submit" onClick={handleCreateWorkspace} disabled={isLoading || !newWorkspaceName}>
                        {isLoading ? "Creating..." : "Create"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
