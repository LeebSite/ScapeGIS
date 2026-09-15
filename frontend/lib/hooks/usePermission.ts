import { useQuery } from '@tanstack/react-query';
import http from '@/lib/api/http';
import { useAuthStore } from '@/lib/store';

/**
 * Hook to check if current user has specific permission(s)
 * 
 * @param permissions - Single permission or array of permissions to check
 * @returns Object with hasPermission boolean and loading state
 * 
 * @example
 * const { hasPermission, isLoading } = usePermission('users.delete');
 * const { hasPermission } = usePermission(['users.read', 'users.update']);
 */
export function usePermission(permissions: string | string[]) {
    const { user } = useAuthStore();
    const permissionsArray = Array.isArray(permissions) ? permissions : [permissions];

    const { data, isLoading } = useQuery({
        queryKey: ['permissions', user?.id],
        queryFn: async () => {
            const response = await http.get<{ permissions: string[] }>('/auth/me/permissions');
            return response.data.permissions;
        },
        enabled: !!user,
        staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    });

    const userPermissions = data || [];

    // Check if user has ALL required permissions
    const hasPermission = permissionsArray.every(perm =>
        userPermissions.includes(perm)
    );

    return {
        hasPermission,
        isLoading,
        permissions: userPermissions,
    };
}

/**
 * Hook to check if current user has ANY of the specified permissions
 * 
 * @param permissions - Array of permissions to check
 * @returns Object with hasAnyPermission boolean and loading state
 * 
 * @example
 * const { hasAnyPermission } = useAnyPermission(['projects.read', 'projects.write']);
 */
export function useAnyPermission(permissions: string[]) {
    const { user } = useAuthStore();

    const { data, isLoading } = useQuery({
        queryKey: ['permissions', user?.id],
        queryFn: async () => {
            const response = await http.get<{ permissions: string[] }>('/auth/me/permissions');
            return response.data.permissions;
        },
        enabled: !!user,
        staleTime: 5 * 60 * 1000,
    });

    const userPermissions = data || [];

    // Check if user has ANY of the required permissions
    const hasAnyPermission = permissions.some(perm =>
        userPermissions.includes(perm)
    );

    return {
        hasAnyPermission,
        isLoading,
        permissions: userPermissions,
    };
}

/**
 * Hook to check if current user has specific role(s)
 * 
 * @param roles - Single role or array of roles to check
 * @returns Boolean indicating if user has the role
 * 
 * @example
 * const isAdmin = useRole('admin');
 * const isAdminOrDeveloper = useRole(['admin', 'developer']);
 */
export function useRole(roles: string | string[]) {
    const { user } = useAuthStore();
    const rolesArray = Array.isArray(roles) ? roles : [roles];

    if (!user) return false;

    return rolesArray.includes(user.role);
}
