import http from "./http";
import type { Project, Layer } from "../types";
import { API_CONFIG } from "./config";
import * as mockProject from "@/lib/mocks/projects";

export interface CreateProjectRequest {
    name: string;
    description?: string;
}

export interface UpdateProjectRequest {
    name?: string;
    description?: string;
}

export const projectAPI = {
    /**
     * Get all projects for current user
     * GET /projects
     */
    getProjects: () =>
        http.get<Project[]>("/projects"),

    /**
     * Create a new project
     * POST /projects
     * Requires permission: projects.create
     */
    createProject: (data: CreateProjectRequest) =>
        http.post<Project>("/projects", data),

    /**
     * Get project by ID
     * GET /projects/{id}
     * Requires permission: projects.read
     */
    getProject: (projectId: string) =>
        http.get<Project>(`/projects/${projectId}`),

    /**
     * Update a project
     * PUT /projects/{id}
     * Requires permission: projects.update
     */
    updateProject: (projectId: string, data: UpdateProjectRequest) =>
        http.put<Project>(`/projects/${projectId}`, data),

    /**
     * Delete a project
     * DELETE /projects/{id}
     * Requires permission: projects.delete
     */
    deleteProject: (projectId: string) =>
        http.delete<{ message: string }>(`/projects/${projectId}`),

    /**
     * Get layers assigned to a project
     * GET /projects/{id}/layers
     * Requires permission: projects.read
     */
    getProjectLayers: (projectId: string) =>
        http.get<Layer[]>(`/projects/${projectId}/layers`),

    /**
     * Assign a layer to a project
     * POST /projects/{id}/layers
     * Requires permission: projects.update
     */
    assignLayer: (projectId: string, layerId: string) =>
        http.post<{ message: string }>(`/projects/${projectId}/layers`, { layer_id: layerId }),

    /**
     * Remove a layer from a project
     * DELETE /projects/{id}/layers/{layerId}
     * Requires permission: projects.update
     */
    removeLayer: (projectId: string, layerId: string) =>
        http.delete<{ message: string }>(`/projects/${projectId}/layers/${layerId}`),
};
