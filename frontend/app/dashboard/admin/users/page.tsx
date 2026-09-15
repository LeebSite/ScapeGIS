"use client";

import { useState, useMemo, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search, Filter, Download } from "lucide-react";
import { AdminStatisticsGrid } from "@/components/dashboard/AdminStatisticsGrid";
import { UsersTable } from "@/components/admin/UsersTable";
import { UserDetailSheet } from "@/components/admin/UserDetailSheet";
import { DeleteUserDialog } from "@/components/admin/DeleteUserDialog";
import {
  useUsers,
  useStatistics,
  useUserDetail,
  useUpdateUserStatus,
  useUpdateUserRole,
  useDeleteUser,
} from "@/lib/hooks/useAdminUsers";
import { useAuthStore } from "@/lib/store";
import { useRouter } from "next/navigation";

type RoleFilter = "all" | "admin" | "developer";
type StatusFilter = "all" | "active" | "inactive";
type AuthProviderFilter = "all" | "local" | "google";

export default function AdminUsersPage() {
  const router = useRouter();
  const { user } = useAuthStore();

  // Check if user is admin
  useEffect(() => {
    if (user && user.role !== "admin") {
      router.push("/dashboard/developer");
    }
  }, [user, router]);

  // State
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState<RoleFilter>("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [authProviderFilter, setAuthProviderFilter] = useState<AuthProviderFilter>("all");
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState<{
    id: string;
    name: string;
    email: string;
  } | null>(null);

  // Queries
  const {
    data: users = [],
    isLoading: usersLoading,
    isError: usersError,
    refetch: refetchUsers,
  } = useUsers();

  const {
    data: statistics,
    isLoading: statisticsLoading,
    isError: statisticsError,
    refetch: refetchStatistics,
  } = useStatistics();

  const {
    data: userDetail,
    isLoading: userDetailLoading,
    isError: userDetailError,
  } = useUserDetail(selectedUserId);

  // Mutations
  const updateStatusMutation = useUpdateUserStatus();
  const updateRoleMutation = useUpdateUserRole();
  const deleteUserMutation = useDeleteUser();

  // Handlers
  const handleToggleStatus = async (userId: string, isActive: boolean) => {
    await updateStatusMutation.mutateAsync({ userId, isActive });
  };

  const handleEditRole = async (userId: string, role: "admin" | "developer") => {
    await updateRoleMutation.mutateAsync({ userId, role });
  };

  const handleDeleteUser = (userId: string, userName: string, userEmail: string) => {
    setUserToDelete({ id: userId, name: userName, email: userEmail });
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!userToDelete) return;

    await deleteUserMutation.mutateAsync(userToDelete.id);

    // Close detail sheet if open
    if (selectedUserId === userToDelete.id) {
      setSelectedUserId(null);
    }

    setDeleteDialogOpen(false);
    setUserToDelete(null);
  };

  // Debounced search
  const [debouncedSearch, setDebouncedSearch] = useState(searchQuery);
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Filtered and sorted users
  const filteredUsers = useMemo(() => {
    return users.filter((user) => {
      // Search filter
      const matchesSearch =
        user.name.toLowerCase().includes(debouncedSearch.toLowerCase()) ||
        user.email.toLowerCase().includes(debouncedSearch.toLowerCase());

      // Role filter
      const matchesRole = roleFilter === "all" || user.role === roleFilter;

      // Status filter
      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "active" && user.is_active) ||
        (statusFilter === "inactive" && !user.is_active);

      // Auth provider filter
      const matchesAuthProvider =
        authProviderFilter === "all" || user.auth_provider === authProviderFilter;

      return matchesSearch && matchesRole && matchesStatus && matchesAuthProvider;
    });
  }, [users, debouncedSearch, roleFilter, statusFilter, authProviderFilter]);

  // Show unauthorized if not admin
  if (user && user.role !== "admin") {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="p-8 max-w-md">
          <h2 className="text-2xl font-bold text-center mb-4">Unauthorized</h2>
          <p className="text-muted-foreground text-center">
            You do not have permission to access this page.
          </p>
          <Button
            className="w-full mt-4"
            onClick={() => router.push("/dashboard/developer")}
          >
            Go to Dashboard
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">User Management</h2>
          <p className="text-muted-foreground mt-1">
            Manage platform users, roles, and permissions
          </p>
        </div>
        <Button variant="outline">
          <Download className="mr-2 h-4 w-4" />
          Export
        </Button>
      </div>

      {/* Statistics Grid */}
      <AdminStatisticsGrid
        data={statistics}
        isLoading={statisticsLoading}
        isError={statisticsError}
        refetch={refetchStatistics}
      />

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Search */}
            <div className="lg:col-span-2 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by name or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Role Filter */}
            <Select value={roleFilter} onValueChange={(value) => setRoleFilter(value as RoleFilter)}>
              <SelectTrigger>
                <SelectValue placeholder="All Roles" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
                <SelectItem value="developer">Developer</SelectItem>
              </SelectContent>
            </Select>

            {/* Status Filter */}
            <Select
              value={statusFilter}
              onValueChange={(value) => setStatusFilter(value as StatusFilter)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>

            {/* Auth Provider Filter */}
            <Select
              value={authProviderFilter}
              onValueChange={(value) => setAuthProviderFilter(value as AuthProviderFilter)}
            >
              <SelectTrigger>
                <SelectValue placeholder="All Providers" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Providers</SelectItem>
                <SelectItem value="local">Local</SelectItem>
                <SelectItem value="google">Google</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Results count */}
          <div className="mt-4 text-sm text-muted-foreground">
            Showing <strong>{filteredUsers.length}</strong> of <strong>{users.length}</strong> users
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <UsersTable
        users={filteredUsers}
        isLoading={usersLoading}
        onViewDetail={setSelectedUserId}
        onToggleStatus={handleToggleStatus}
        onEditRole={handleEditRole}
        onDeleteUser={handleDeleteUser}
      />

      {/* User Detail Sheet */}
      <UserDetailSheet
        userId={selectedUserId}
        open={!!selectedUserId}
        onOpenChange={(open) => !open && setSelectedUserId(null)}
        userDetail={userDetail}
        isLoading={userDetailLoading}
        isError={userDetailError}
        onToggleStatus={handleToggleStatus}
        onEditRole={handleEditRole}
        onDeleteUser={handleDeleteUser}
      />

      {/* Delete User Dialog */}
      {userToDelete && (
        <DeleteUserDialog
          userId={userToDelete.id}
          userName={userToDelete.name}
          userEmail={userToDelete.email}
          open={deleteDialogOpen}
          onOpenChange={setDeleteDialogOpen}
          onConfirm={handleConfirmDelete}
        />
      )}
    </div>
  );
}
