import http from "./http";
import type { GISDataset, GISLayer, GeoJSONFeatureCollection } from "@/lib/types/gis";

export interface GISAccessWorkspaceInfo {
    id: string;
    name: string;
    slug: string;
}

export interface GISAccessDatasetInfo {
    id: string;
    name: string;
    file_type: string;
    total_layers: number;
    total_features: number;
    geometry_type?: string;
    status: string;
}

export interface GISAccessGranterInfo {
    id: string;
    email: string;
    name?: string;
}

export interface GISAccessGrant {
    id: string;
    workspace_id: string;
    dataset_id: string;
    is_active: boolean;
    notes?: string;
    granted_at: string;
    revoked_at?: string;
    workspace?: GISAccessWorkspaceInfo;
    dataset?: GISAccessDatasetInfo;
    granter?: GISAccessGranterInfo;
}

export interface GISAccessListResponse {
    total: number;
    items: GISAccessGrant[];
}

export interface GrantAccessPayload {
    workspace_id: string;
    dataset_id: string;
    notes?: string;
}

export interface RevokeAccessPayload {
    workspace_id: string;
    dataset_id: string;
    reason?: string;
}

export interface AuthorizedDataset extends GISDataset {
    granted_at?: string;
}

export const GISAccessService = {
    /**
     * Admin: List all access grants across the platform
     */
    async listAllGrants(params?: {
        skip?: number;
        limit?: number;
        workspace_id?: string;
        dataset_id?: string;
        active_only?: boolean;
    }): Promise<GISAccessListResponse> {
        const response = await http.get<GISAccessListResponse>("/admin/gis-access", { params });
        return response.data;
    },

    /**
     * Admin: Grant access to a GIS dataset for a specific workspace
     */
    async grantAccess(payload: GrantAccessPayload): Promise<GISAccessGrant> {
        const response = await http.post<GISAccessGrant>("/admin/gis-access/grant", payload);
        return response.data;
    },

    /**
     * Admin: Revoke a workspace's access to a GIS dataset
     */
    async revokeAccess(payload: RevokeAccessPayload): Promise<GISAccessGrant> {
        const response = await http.post<GISAccessGrant>("/admin/gis-access/revoke", payload);
        return response.data;
    },

    /**
     * Admin: Get grants for a specific workspace
     */
    async getGrantsByWorkspace(workspaceId: string, activeOnly = true): Promise<GISAccessGrant[]> {
        const response = await http.get<GISAccessGrant[]>(`/admin/gis-access/workspace/${workspaceId}`, {
            params: { active_only: activeOnly },
        });
        return response.data;
    },

    /**
     * Admin: Get grants for a specific dataset
     */
    async getGrantsByDataset(datasetId: string, activeOnly = true): Promise<GISAccessGrant[]> {
        const response = await http.get<GISAccessGrant[]>(`/admin/gis-access/dataset/${datasetId}`, {
            params: { active_only: activeOnly },
        });
        return response.data;
    },

    /**
     * Admin: Get all workspaces for grant selection dropdown
     */
    async getWorkspacesForGrant(): Promise<GISAccessWorkspaceInfo[]> {
        const response = await http.get<GISAccessWorkspaceInfo[]>("/admin/gis-access/workspaces");
        return response.data;
    },

    /**
     * Admin: Get all completed datasets for grant selection dropdown
     */
    async getDatasetsForGrant(): Promise<GISAccessDatasetInfo[]> {
        const response = await http.get<GISAccessDatasetInfo[]>("/admin/gis-access/datasets");
        return response.data;
    },

    /**
     * Workspace: Get datasets authorized for a workspace
     */
    async getWorkspaceAuthorizedDatasets(workspaceId: string): Promise<AuthorizedDataset[]> {
        const response = await http.get<AuthorizedDataset[]>(`/workspaces/${workspaceId}/gis/datasets`);
        return response.data;
    },

    /**
     * Workspace: Get layers of an authorized dataset in a workspace
     */
    async getWorkspaceDatasetLayers(workspaceId: string, datasetId: string): Promise<GISLayer[]> {
        const response = await http.get<GISLayer[]>(`/workspaces/${workspaceId}/gis/datasets/${datasetId}/layers`);
        return response.data;
    },

    /**
     * Workspace: Get layer GeoJSON with workspace entitlement verification
     */
    async getWorkspaceLayerGeoJSON(workspaceId: string, layerId: string): Promise<GeoJSONFeatureCollection> {
        const response = await http.get<GeoJSONFeatureCollection>(`/workspaces/${workspaceId}/gis/layers/${layerId}/geojson`);
        return response.data;
    },
};

export default GISAccessService;