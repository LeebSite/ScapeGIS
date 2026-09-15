import http from "./http";
import type { Workspace, WorkspaceMember } from "../types";
import { API_CONFIG } from "./config";
import * as mockWorkspace from "@/lib/mocks/workspaces";

export interface CreateWorkspaceRequest {
    name: string;
    description?: string;
}

export interface InviteMemberRequest {
    email: string;
    role: "admin" | "member";
}

export interface WorkspaceUsageResponse {
    prompts_used_this_month: number;
    prompts_limit: number;
    projects_count: number;
    projects_limit: number;
    members_count: number;
    members_limit: number;
}

export const workspaceAPI = {
    /**
     * Get all workspaces for current user
     * GET /workspaces
     */
    getWorkspaces: () => http.get<Workspace[]>("/workspaces"),

    /**
     * Create a new workspace
     * POST /workspaces
     */
    createWorkspace: (data: CreateWorkspaceRequest) =>
        http.post<Workspace>("/workspaces", data),

    /**
     * Update workspace
     * PUT /workspaces/{id}
     */
    updateWorkspace: (id: string, data: Partial<CreateWorkspaceRequest>) =>
        http.put<Workspace>(`/workspaces/${id}`, data),

    /**
     * Delete workspace
     * DELETE /workspaces/{id}
     */
    deleteWorkspace: (id: string) =>
        http.delete<{ message: string }>(`/workspaces/${id}`),

    /**
     * Get workspace members
     * GET /workspaces/{id}/members
     */
    getMembers: (workspaceId: string) =>
        http.get<WorkspaceMember[]>(`/workspaces/${workspaceId}/members`),

    /**
     * Invite a member to workspace
     * POST /workspaces/{id}/invite
     */
    inviteMember: (workspaceId: string, data: InviteMemberRequest) =>
        http.post<{ message: string; invitation_id: string }>(
            `/workspaces/${workspaceId}/invite`,
            data
        ),

    /**
     * Remove a member from workspace
     * DELETE /workspaces/{id}/members/{memberId}
     */
    removeMember: (workspaceId: string, memberId: string) =>
        http.delete<{ message: string }>(
            `/workspaces/${workspaceId}/members/${memberId}`
        ),

    /**
     * Get workspace usage stats
     * GET /workspaces/{id}/usage
     */
    getUsage: (workspaceId: string) =>
        http.get<WorkspaceUsageResponse>(`/workspaces/${workspaceId}/usage`),
};
