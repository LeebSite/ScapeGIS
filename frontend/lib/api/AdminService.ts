import { fetchAPI } from './authService';

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'developer';
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at?: string;
  last_login_at?: string;
  // Additional fields that might be returned
  auth_provider?: string;
  workspace_count?: number;
}

export type UserListResponse = User;

export interface UserStats {
  total_users: number;
  active_users: number;
  verified_users: number;
  new_users_last_30_days: number;
  // Optional legacy fields if backend returns them
  inactive_users?: number;
  users_by_role?: Record<string, number>;
  users_by_auth_provider?: Record<string, number>;
  total_workspaces?: number;
}

export type UserStatisticsResponse = UserStats;

export interface WorkspaceSummary {
  id: string;
  name: string;
  role: string;
  subscription_name: string | null;
  member_count: number;
  project_count: number;
  created_at: string;
}

export interface UserDetailResponse extends User {
  workspaces: WorkspaceSummary[];
  auth_provider?: string;
  avatar_url?: string;
}

// 1. Get All Users (Table)
export async function getAdminUsers() {
  return fetchAPI<User[]>('/admin/users');
}

// 2. Get User Statistics (Cards)
export async function getAdminStats() {
  return fetchAPI<UserStats>('/admin/users/statistics');
}

// 2.5 Get User Detail (Preserved for compatibility)
export async function getAdminUserDetail(userId: string) {
  return fetchAPI<UserDetailResponse>(`/admin/users/${userId}`);
}

// 3. Toggle User Status (Active/Inactive)
export async function updateUserStatus(userId: string, isActive: boolean) {
  return fetchAPI(`/admin/users/${userId}/status`, {
    method: 'PUT',
    body: JSON.stringify({ is_active: isActive })
  });
}

// 4. Update User Role
export async function updateUserRole(userId: string, role: 'admin' | 'developer') {
  return fetchAPI(`/admin/users/${userId}/role`, {
    method: 'PUT',
    body: JSON.stringify({ role })
  });
}

// 5. Delete User
export async function deleteUser(userId: string) {
  return fetchAPI(`/admin/users/${userId}`, {
    method: 'DELETE'
  });
}

// 6. Get Audit Logs
export async function getAuditLogs(params?: { action?: string; user_id?: string }) {
  const qs = new URLSearchParams(params as any).toString();
  return fetchAPI(`/admin/audit-logs?${qs}`);
}

// Backward compatibility object
export const adminAPI = {
  getAllUsers: getAdminUsers,
  getUserStatistics: getAdminStats,
  getUserDetail: getAdminUserDetail,
  updateUserStatus: (userId: string, data: { is_active: boolean }) => updateUserStatus(userId, data.is_active),
  updateUserRole: (userId: string, data: { role: 'admin' | 'developer' }) => updateUserRole(userId, data.role),
  deleteUser: deleteUser
};
