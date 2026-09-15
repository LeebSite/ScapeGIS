"use client";

import { useEffect, useState } from "react";
import { invitationAPI } from "@/lib/api";
import type { WorkspaceInvitation } from "@/lib/types";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { XCircle } from "lucide-react";

interface PendingInvitationsProps {
    workspaceId: string;
}

export function PendingInvitations({ workspaceId }: PendingInvitationsProps) {
    const [invitations, setInvitations] = useState<WorkspaceInvitation[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const fetchInvitations = async () => {
        try {
            const res = await invitationAPI.getPendingInvitations(workspaceId);
            setInvitations(res.data);
        } catch (error) {
            console.error("Failed to fetch invitations:", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (workspaceId) {
            fetchInvitations();
        }
    }, [workspaceId]);

    const handleCancelInvitation = async (token: string) => {
        if (!confirm("Are you sure you want to cancel this invitation?")) return;
        try {
            await invitationAPI.declineInvitation(token);
            setInvitations(invitations.filter((i) => i.token !== token));
        } catch (error) {
            console.error("Failed to cancel invitation:", error);
        }
    };

    if (isLoading) return <div>Loading invitations...</div>;
    if (invitations.length === 0) return null;

    return (
        <div className="space-y-4 mt-8">
            <h3 className="text-lg font-medium">Pending Invitations</h3>
            <div className="rounded-md border">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Email</TableHead>
                            <TableHead>Role</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Sent At</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {invitations.map((invitation) => (
                            <TableRow key={invitation.id}>
                                <TableCell>{invitation.email}</TableCell>
                                <TableCell>
                                    <Badge variant="outline">{invitation.role}</Badge>
                                </TableCell>
                                <TableCell>
                                    <Badge variant="secondary">{invitation.status}</Badge>
                                </TableCell>
                                <TableCell>
                                    {new Date(invitation.created_at).toLocaleDateString()}
                                </TableCell>
                                <TableCell className="text-right">
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => handleCancelInvitation(invitation.token)}
                                        title="Cancel Invitation"
                                    >
                                        <XCircle className="h-4 w-4 text-muted-foreground" />
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>
        </div>
    );
}
