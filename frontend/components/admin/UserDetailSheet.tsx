"use client";

import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
} from "@/components/ui/sheet";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    CheckCircle,
    XCircle,
    Calendar,
    Mail,
    Shield,
    Key,
    Briefcase,
    Users,
    FolderKanban,
    Loader2,
    AlertCircle,
} from "lucide-react";
import { format } from "date-fns";
import { useState } from "react";
import type { UserDetailResponse } from "@/lib/api/AdminService";
import { RoleBadge } from "./RoleBadge";
import { AuthProviderBadge } from "./AuthProviderBadge";
import { StatusToggle } from "./StatusToggle";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface UserDetailSheetProps {
    userId: string | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    userDetail: UserDetailResponse | undefined;
    isLoading: boolean;
    isError: boolean;
    onToggleStatus: (userId: string, isActive: boolean) => Promise<void>;
    onEditRole: (userId: string, role: "admin" | "developer") => Promise<void>;
    onDeleteUser: (userId: string, userName: string, userEmail: string) => void;
}

export function UserDetailSheet({
    userId,
    open,
    onOpenChange,
    userDetail,
    isLoading,
    isError,
    onToggleStatus,
    onEditRole,
    onDeleteUser,
}: UserDetailSheetProps) {
    const [isEditingRole, setIsEditingRole] = useState(false);

    const getInitials = (name: string) => {
        return name
            .split(" ")
            .map((n) => n[0])
            .join("")
            .toUpperCase()
            .slice(0, 2);
    };

    const handleRoleChange = async (newRole: "admin" | "developer") => {
        if (!userDetail) return;
        setIsEditingRole(true);
        try {
            await onEditRole(userDetail.id, newRole);
        } finally {
            setIsEditingRole(false);
        }
    };

    return (
        <Sheet open={open} onOpenChange={onOpenChange}>
            <SheetContent className="w-full sm:max-w-xl overflow-y-auto">
                {isLoading && (
                    <div className="space-y-6">
                        <div className="flex items-center gap-4">
                            <Skeleton className="h-16 w-16 rounded-full" />
                            <div className="space-y-2 flex-1">
                                <Skeleton className="h-6 w-48" />
                                <Skeleton className="h-4 w-64" />
                            </div>
                        </div>
                        <Skeleton className="h-32 w-full" />
                        <Skeleton className="h-48 w-full" />
                    </div>
                )}

                {isError && (
                    <div className="flex flex-col items-center justify-center h-full space-y-4">
                        <AlertCircle className="h-12 w-12 text-destructive" />
                        <div className="text-center">
                            <h3 className="font-semibold text-lg">Failed to load user details</h3>
                            <p className="text-sm text-muted-foreground mt-1">
                                There was an error loading the user information
                            </p>
                        </div>
                    </div>
                )}

                {userDetail && !isLoading && !isError && (
                    <>
                        <SheetHeader>
                            <SheetTitle>User Details</SheetTitle>
                            <SheetDescription>
                                View and manage user information
                            </SheetDescription>
                        </SheetHeader>

                        <div className="space-y-6 mt-6">
                            {/* User Header */}
                            <div className="flex items-start gap-4">
                                <Avatar className="h-16 w-16">
                                    <AvatarFallback className="text-lg">
                                        {getInitials(userDetail.name)}
                                    </AvatarFallback>
                                </Avatar>
                                <div className="flex-1 space-y-2">
                                    <h3 className="text-xl font-semibold">{userDetail.name}</h3>
                                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                        <Mail className="h-4 w-4" />
                                        {userDetail.email}
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <RoleBadge role={userDetail.role} />
                                        <AuthProviderBadge provider={(userDetail.auth_provider || 'local') as "local" | "google"} />
                                        {userDetail.is_verified ? (
                                            <Badge variant="outline" className="gap-1 text-green-600">
                                                <CheckCircle className="h-3 w-3" />
                                                Verified
                                            </Badge>
                                        ) : (
                                            <Badge variant="outline" className="gap-1 text-muted-foreground">
                                                <XCircle className="h-3 w-3" />
                                                Not Verified
                                            </Badge>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <Separator />

                            {/* Basic Information */}
                            <div className="space-y-4">
                                <h4 className="font-semibold">Basic Information</h4>
                                <div className="grid gap-3">
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-muted-foreground">User ID</span>
                                        <span className="text-sm font-mono">{userDetail.id.slice(0, 8)}...</span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-muted-foreground">Created</span>
                                        <span className="text-sm">
                                            {format(new Date(userDetail.created_at), "MMM dd, yyyy HH:mm")}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-muted-foreground">Last Updated</span>
                                        <span className="text-sm">
                                            {userDetail.updated_at
                                                ? format(new Date(userDetail.updated_at), "MMM dd, yyyy HH:mm")
                                                : "N/A"}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm text-muted-foreground">Last Login</span>
                                        <span className="text-sm">
                                            {userDetail.last_login_at
                                                ? format(new Date(userDetail.last_login_at), "MMM dd, yyyy HH:mm")
                                                : "Never"}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <Separator />

                            {/* Actions */}
                            <div className="space-y-4">
                                <h4 className="font-semibold">Actions</h4>

                                <div className="space-y-3">
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm font-medium">Role</span>
                                        <div className="flex items-center gap-2">
                                            <Select
                                                value={userDetail.role}
                                                onValueChange={(value) => handleRoleChange(value as "admin" | "developer")}
                                                disabled={isEditingRole}
                                            >
                                                <SelectTrigger className="w-32">
                                                    <SelectValue />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="developer">Developer</SelectItem>
                                                    <SelectItem value="admin">Admin</SelectItem>
                                                </SelectContent>
                                            </Select>
                                            {isEditingRole && <Loader2 className="h-4 w-4 animate-spin" />}
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <span className="text-sm font-medium">Account Status</span>
                                        <StatusToggle
                                            userId={userDetail.id}
                                            isActive={userDetail.is_active}
                                            onToggle={onToggleStatus}
                                        />
                                    </div>

                                    <Separator />

                                    <Button
                                        variant="destructive"
                                        className="w-full"
                                        onClick={() => onDeleteUser(userDetail.id, userDetail.name, userDetail.email)}
                                    >
                                        Delete User
                                    </Button>
                                </div>
                            </div>

                            <Separator />

                            {/* Workspaces */}
                            <div className="space-y-4">
                                <div className="flex items-center gap-2">
                                    <Briefcase className="h-4 w-4" />
                                    <h4 className="font-semibold">Workspaces ({userDetail.workspaces?.length || 0})</h4>
                                </div>

                                {(!userDetail.workspaces || userDetail.workspaces.length === 0) ? (
                                    <p className="text-sm text-muted-foreground py-4 text-center">
                                        No workspaces found
                                    </p>
                                ) : (
                                    <div className="space-y-3">
                                        {userDetail.workspaces.map((workspace) => (
                                            <Card key={workspace.id}>
                                                <CardHeader className="pb-3">
                                                    <CardTitle className="text-base">{workspace.name}</CardTitle>
                                                </CardHeader>
                                                <CardContent className="space-y-2">
                                                    <div className="flex items-center justify-between text-sm">
                                                        <span className="text-muted-foreground">Role</span>
                                                        <Badge variant="outline" className="capitalize">
                                                            {workspace.role}
                                                        </Badge>
                                                    </div>
                                                    {workspace.subscription_name && (
                                                        <div className="flex items-center justify-between text-sm">
                                                            <span className="text-muted-foreground">Subscription</span>
                                                            <Badge className="capitalize">{workspace.subscription_name}</Badge>
                                                        </div>
                                                    )}
                                                    <div className="flex items-center gap-4 text-sm text-muted-foreground pt-2">
                                                        <div className="flex items-center gap-1">
                                                            <Users className="h-3 w-3" />
                                                            {workspace.member_count} members
                                                        </div>
                                                        <div className="flex items-center gap-1">
                                                            <FolderKanban className="h-3 w-3" />
                                                            {workspace.project_count} projects
                                                        </div>
                                                    </div>
                                                    <div className="text-xs text-muted-foreground pt-1">
                                                        Joined {format(new Date(workspace.created_at), "MMM dd, yyyy")}
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </>
                )}
            </SheetContent>
        </Sheet>
    );
}
