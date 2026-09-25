import http from "./http";

export interface Workspace {
    id: string;
    name: string;
    slug: string;
    description?: string;
    logo_url?: string;
    role: "owner" | "member";
    member_count: number;
    created_at: string;
}

export interface WorkspaceDetail extends Workspace {
    owner_id: string;
    updated_at: string;
}

export interface WorkspaceMember {
    id: string;
    workspace_id: string;
    user_id: string;
    role: "owner" | "member";
    joined_at: string;
    user_name?: string;
    user_email?: string;
    user_avatar_url?: string;
}

export interface CreateWorkspaceRequest {
    name: string;
    description?: string;
}

export interface UpdateWorkspaceRequest {
    name?: string;
    description?: string;
    logo_url?: string;
}

export interface InviteMemberRequest {
    email: string;
}

export interface InviteMemberResponse {
    message: string;
    token: string;
    invitation_id: string;
}

export interface AcceptInvitationResponse {
    message: string;
    workspace_id: string;
    workspace_name: string;
}

export const workspaceAPI = {
    /** GET /workspaces - list all workspaces for current user */
    getWorkspaces: () =>
        http.get<Workspace[]>("/workspaces"),

    /** POST /workspaces - create workspace (developer only) */
    createWorkspace: (data: CreateWorkspaceRequest) =>
        http.post<{ message: string; workspace_id: string }>("/workspaces", data),

    /** GET /workspaces/{id} - workspace detail */
    getWorkspace: (id: string) =>
        http.get<WorkspaceDetail>(`/workspaces/${id}`),

    /** PATCH /workspaces/{id} - update workspace (owner only) */
    updateWorkspace: (id: string, data: UpdateWorkspaceRequest) =>
        http.patch<WorkspaceDetail>(`/workspaces/${id}`, data),

    /** DELETE /workspaces/{id} - delete workspace (owner only) */
    deleteWorkspace: (id: string) =>
        http.delete<{ message: string }>(`/workspaces/${id}`),

    /** GET /workspaces/{id}/members */
    getMembers: (workspaceId: string) =>
        http.get<WorkspaceMember[]>(`/workspaces/${workspaceId}/members`),

    /** POST /workspaces/{id}/invite - invite by email (owner only) */
    inviteMember: (workspaceId: string, data: InviteMemberRequest) =>
        http.post<InviteMemberResponse>(`/workspaces/${workspaceId}/invite`, data),

    /** POST /invitations/{token}/accept - accept invitation */
    acceptInvitation: (token: string) =>
        http.post<AcceptInvitationResponse>(`/invitations/${token}/accept`, {}),
};
