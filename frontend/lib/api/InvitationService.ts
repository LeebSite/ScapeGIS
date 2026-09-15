import http from "./http";
import type { WorkspaceInvitation, Workspace, WorkspaceMember } from "../types";

export interface AcceptInvitationResponse {
    workspace: Workspace;
    member: WorkspaceMember;
}

export const invitationAPI = {
    /**
     * Get pending invitations for a workspace
     * GET /workspaces/{id}/invitations
     */
    getPendingInvitations: (workspaceId: string) =>
        http.get<WorkspaceInvitation[]>(`/workspaces/${workspaceId}/invitations`),

    /**
     * Accept an invitation
     * POST /invitations/{token}/accept
     */
    acceptInvitation: (token: string) =>
        http.post<AcceptInvitationResponse>(`/invitations/${token}/accept`),

    /**
     * Decline/Cancel an invitation
     * DELETE /invitations/{token}
     */
    declineInvitation: (token: string) =>
        http.delete<{ message: string }>(`/invitations/${token}`),
};
