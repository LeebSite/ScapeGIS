"use client";

import { useEffect, useState } from "react";
import { workspaceAPI } from "@/lib/api";
import type { WorkspaceMember } from "@/lib/types";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Trash2 } from "lucide-react";
import { useAuthStore } from "@/lib/store";

interface TeamMembersListProps {
    workspaceId: string;
}

export function TeamMembersList({ workspaceId }: TeamMembersListProps) {
    const [members, setMembers] = useState<WorkspaceMember[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const { user } = useAuthStore();

    const fetchMembers = async () => {
        try {
            const res = await workspaceAPI.getMembers(workspaceId);
            setMembers(res.data);
        } catch (error) {
            console.error("Failed to fetch members:", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (workspaceId) {
            fetchMembers();
        }
    }, [workspaceId]);

    const handleRemoveMember = async (memberId: string) => {
        if (!confirm("Are you sure you want to remove this member?")) return;
        try {
            await workspaceAPI.removeMember(workspaceId, memberId);
            setMembers(members.filter((m) => m.id !== memberId));
        } catch (error) {
            console.error("Failed to remove member:", error);
        }
    };

    if (isLoading) return <div>Loading members...</div>;

    return (
        <div className="space-y-4">
            <div className="rounded-md border">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>User</TableHead>
                            <TableHead>Role</TableHead>
                            <TableHead>Joined At</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {members.map((member) => (
                            <TableRow key={member.id}>
                                <TableCell className="flex items-center gap-2">
                                    <Avatar className="h-8 w-8">
                                        <AvatarImage src={member.user?.avatar_url} />
                                        <AvatarFallback>
                                            {member.user?.name?.charAt(0).toUpperCase() || "?"}
                                        </AvatarFallback>
                                    </Avatar>
                                    <div className="flex flex-col">
                                        <span className="font-medium">{member.user?.name}</span>
                                        <span className="text-xs text-muted-foreground">
                                            {member.user?.email}
                                        </span>
                                    </div>
                                </TableCell>
                                <TableCell>
                                    <Badge variant={member.role === "owner" ? "default" : "secondary"}>
                                        {member.role}
                                    </Badge>
                                </TableCell>
                                <TableCell>
                                    {new Date(member.joined_at).toLocaleDateString()}
                                </TableCell>
                                <TableCell className="text-right">
                                    {member.role !== "owner" && user?.id !== member.user_id && (
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => handleRemoveMember(member.id)}
                                        >
                                            <Trash2 className="h-4 w-4 text-destructive" />
                                        </Button>
                                    )}
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>
        </div>
    );
}
