"use client";

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
    DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { MoreVertical, CheckCircle, XCircle, Eye, Edit, Trash2 } from "lucide-react";
import { format } from "date-fns";
import type { UserListResponse } from "@/lib/api/AdminService";
import { RoleBadge } from "./RoleBadge";
import { AuthProviderBadge } from "./AuthProviderBadge";
import { StatusToggle } from "./StatusToggle";
import { useState } from "react";
import { Card } from "@/components/ui/card";

interface UsersTableProps {
    users: UserListResponse[];
    isLoading: boolean;
    onViewDetail: (userId: string) => void;
    onToggleStatus: (userId: string, isActive: boolean) => Promise<void>;
    onEditRole: (userId: string, role: "admin" | "developer") => Promise<void>;
    onDeleteUser: (userId: string, userName: string, userEmail: string) => void;
}

export function UsersTable({
    users,
    isLoading,
    onViewDetail,
    onToggleStatus,
    onEditRole,
    onDeleteUser,
}: UsersTableProps) {
    const [sortColumn, setSortColumn] = useState<keyof UserListResponse | null>(null);
    const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

    const handleSort = (column: keyof UserListResponse) => {
        if (sortColumn === column) {
            setSortDirection(sortDirection === "asc" ? "desc" : "asc");
        } else {
            setSortColumn(column);
            setSortDirection("asc");
        }
    };

    const sortedUsers = [...users].sort((a, b) => {
        if (!sortColumn) return 0;

        const aValue = a[sortColumn];
        const bValue = b[sortColumn];

        if (aValue === null || aValue === undefined) return 1;
        if (bValue === null || bValue === undefined) return -1;

        if (typeof aValue === "string" && typeof bValue === "string") {
            return sortDirection === "asc"
                ? aValue.localeCompare(bValue)
                : bValue.localeCompare(aValue);
        }

        if (typeof aValue === "number" && typeof bValue === "number") {
            return sortDirection === "asc" ? aValue - bValue : bValue - aValue;
        }

        return 0;
    });

    const getInitials = (name: string) => {
        return name
            .split(" ")
            .map((n) => n[0])
            .join("")
            .toUpperCase()
            .slice(0, 2);
    };

    if (isLoading) {
        return (
            <Card>
                <div className="p-6 space-y-4">
                    {Array.from({ length: 5 }).map((_, i) => (
                        <div key={i} className="flex items-center gap-4">
                            <Skeleton className="h-10 w-10 rounded-full" />
                            <div className="space-y-2 flex-1">
                                <Skeleton className="h-4 w-48" />
                                <Skeleton className="h-3 w-32" />
                            </div>
                            <Skeleton className="h-8 w-20" />
                            <Skeleton className="h-8 w-20" />
                        </div>
                    ))}
                </div>
            </Card>
        );
    }

    if (users.length === 0) {
        return (
            <Card>
                <div className="p-12 text-center">
                    <p className="text-muted-foreground">No users found</p>
                </div>
            </Card>
        );
    }

    return (
        <Card>
            <div className="overflow-x-auto">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead
                                className="cursor-pointer hover:bg-muted/50"
                                onClick={() => handleSort("name")}
                            >
                                User
                            </TableHead>
                            <TableHead
                                className="cursor-pointer hover:bg-muted/50"
                                onClick={() => handleSort("role")}
                            >
                                Role
                            </TableHead>
                            <TableHead>Auth Provider</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Verified</TableHead>
                            <TableHead
                                className="cursor-pointer hover:bg-muted/50"
                                onClick={() => handleSort("workspace_count")}
                            >
                                Workspaces
                            </TableHead>
                            <TableHead
                                className="cursor-pointer hover:bg-muted/50"
                                onClick={() => handleSort("last_login_at")}
                            >
                                Last Login
                            </TableHead>
                            <TableHead>Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {sortedUsers.map((user) => (
                            <TableRow key={user.id} className="hover:bg-muted/50">
                                <TableCell>
                                    <div className="flex items-center gap-3">
                                        <Avatar>
                                            <AvatarFallback>{getInitials(user.name)}</AvatarFallback>
                                        </Avatar>
                                        <div>
                                            <div className="font-medium">{user.name}</div>
                                            <div className="text-sm text-muted-foreground">{user.email}</div>
                                        </div>
                                    </div>
                                </TableCell>
                                <TableCell>
                                    <RoleBadge role={user.role} />
                                </TableCell>
                                <TableCell>
                                    <AuthProviderBadge provider={user.auth_provider as "local" | "google" || "local"} />
                                </TableCell>
                                <TableCell>
                                    <StatusToggle
                                        userId={user.id}
                                        isActive={user.is_active}
                                        onToggle={onToggleStatus}
                                    />
                                </TableCell>
                                <TableCell>
                                    {user.is_verified ? (
                                        <CheckCircle className="h-4 w-4 text-green-600" />
                                    ) : (
                                        <XCircle className="h-4 w-4 text-muted-foreground" />
                                    )}
                                </TableCell>
                                <TableCell>
                                    <Badge variant="outline">{user.workspace_count ?? 0}</Badge>
                                </TableCell>
                                <TableCell>
                                    <div className="text-sm">
                                        {user.last_login_at
                                            ? format(new Date(user.last_login_at), "MMM dd, yyyy HH:mm")
                                            : "Never"}
                                    </div>
                                </TableCell>
                                <TableCell>
                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <Button variant="ghost" size="icon">
                                                <MoreVertical className="h-4 w-4" />
                                            </Button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="end">
                                            <DropdownMenuItem onClick={() => onViewDetail(user.id)}>
                                                <Eye className="mr-2 h-4 w-4" />
                                                View Details
                                            </DropdownMenuItem>
                                            <DropdownMenuItem
                                                onClick={() =>
                                                    onEditRole(
                                                        user.id,
                                                        user.role === "admin" ? "developer" : "admin"
                                                    )
                                                }
                                            >
                                                <Edit className="mr-2 h-4 w-4" />
                                                Change Role
                                            </DropdownMenuItem>
                                            <DropdownMenuSeparator />
                                            <DropdownMenuItem
                                                className="text-destructive focus:text-destructive"
                                                onClick={() => onDeleteUser(user.id, user.name, user.email)}
                                            >
                                                <Trash2 className="mr-2 h-4 w-4" />
                                                Delete User
                                            </DropdownMenuItem>
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>
        </Card>
    );
}
