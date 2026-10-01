import http from "./http";
import type { Project, ProjectDetail, ProjectLayer } from "../types";

export interface CreateProjectRequest {
    workspace_id: string;
    name: string;
    description?: string;
    project_type?: string;
    city?: string;
    province?: string;
}

export interface UpdateProjectRequest {
    name?: string;
    description?: string;
    project_type?: string;
    city?: string;
    province?: string;
    status?: string;
}

export interface AddProjectLayerRequest {
    dataset_id: string;
    layer_id: string;
}

export interface UpdateProjectLayerRequest {
    is_visible?: boolean;
    opacity?: number;
    layer_order?: number;
}

export interface ProjectListResponse {
    items: Project[];
    total: number;
}

export const projectAPI = {
    /** GET /projects?workspace_id=... */
    getProjects: (workspaceId: string) =>
        http.get<ProjectListResponse>("/projects", { params: { workspace_id: workspaceId } }),

    /** POST /projects */
    createProject: (data: CreateProjectRequest) =>
        http.post<Project>("/projects", data),

    /** GET /projects/{id} */
    getProject: (projectId: string) =>
        http.get<ProjectDetail>(`/projects/${projectId}`),

    /** PATCH /projects/{id} */
    updateProject: (projectId: string, data: UpdateProjectRequest) =>
        http.patch<ProjectDetail>(`/projects/${projectId}`, data),

    /** DELETE /projects/{id} */
    deleteProject: (projectId: string) =>
        http.delete<{ message: string }>(`/projects/${projectId}`),

    /** POST /projects/{id}/archive */
    archiveProject: (projectId: string) =>
        http.post<{ message: string }>(`/projects/${projectId}/archive`, {}),

    // ---- Layer management ----

    /** GET /projects/{id}/layers */
    getProjectLayers: (projectId: string) =>
        http.get<ProjectLayer[]>(`/projects/${projectId}/layers`),

    /** POST /projects/{id}/layers */
    addProjectLayer: (projectId: string, data: AddProjectLayerRequest) =>
        http.post<ProjectLayer>(`/projects/${projectId}/layers`, data),

    /** PATCH /projects/{id}/layers/{layerId} */
    updateProjectLayer: (projectId: string, layerId: string, data: UpdateProjectLayerRequest) =>
        http.patch<ProjectLayer>(`/projects/${projectId}/layers/${layerId}`, data),

    /** DELETE /projects/{id}/layers/{layerId} */
    removeProjectLayer: (projectId: string, layerId: string) =>
        http.delete<{ message: string }>(`/projects/${projectId}/layers/${layerId}`),
};
