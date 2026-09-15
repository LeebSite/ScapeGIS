import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectAPI, CreateProjectRequest, UpdateProjectRequest } from '@/lib/api/ProjectService';
import type { Project, Layer } from '@/lib/types';
import { toast } from 'sonner'; // or your toast library

/**
 * Hook to fetch all projects for current user
 * 
 * @example
 * const { projects, isLoading, error } = useProjects();
 */
export function useProjects() {
    const { data, isLoading, error, refetch } = useQuery({
        queryKey: ['projects'],
        queryFn: async () => {
            const response = await projectAPI.getProjects();
            return response.data;
        },
    });

    return {
        projects: data || [],
        isLoading,
        error,
        refetch,
    };
}

/**
 * Hook to fetch a single project by ID
 * 
 * @param projectId - ID of the project to fetch
 * @example
 * const { project, isLoading } = useProject(projectId);
 */
export function useProject(projectId: string | undefined) {
    const { data, isLoading, error } = useQuery({
        queryKey: ['projects', projectId],
        queryFn: async () => {
            if (!projectId) throw new Error('Project ID is required');
            const response = await projectAPI.getProject(projectId);
            return response.data;
        },
        enabled: !!projectId, // Only fetch if projectId exists
    });

    return {
        project: data,
        isLoading,
        error,
    };
}

/**
 * Hook to create a new project
 * 
 * @example
 * const { createProject, isCreating } = useCreateProject();
 * await createProject({ name: 'New Project', description: 'Description' });
 */
export function useCreateProject() {
    const queryClient = useQueryClient();

    const mutation = useMutation({
        mutationFn: async (data: CreateProjectRequest) => {
            const response = await projectAPI.createProject(data);
            return response.data;
        },
        onSuccess: (newProject) => {
            // Invalidate and refetch projects list
            queryClient.invalidateQueries({ queryKey: ['projects'] });
            toast.success('Project created successfully');
        },
        onError: (error: any) => {
            const message = error.response?.data?.message ||
                error.response?.data?.detail ||
                'Failed to create project';
            toast.error(message);
        },
    });

    return {
        createProject: mutation.mutateAsync,
        isCreating: mutation.isPending,
        error: mutation.error,
    };
}

/**
 * Hook to update an existing project
 * 
 * @example
 * const { updateProject, isUpdating } = useUpdateProject();
 * await updateProject({ projectId: '123', updates: { name: 'Updated Name' } });
 */
export function useUpdateProject() {
    const queryClient = useQueryClient();

    const mutation = useMutation({
        mutationFn: async ({ projectId, updates }: { projectId: string; updates: UpdateProjectRequest }) => {
            const response = await projectAPI.updateProject(projectId, updates);
            return response.data;
        },
        onSuccess: (updatedProject, variables) => {
            // Invalidate both the list and the specific project
            queryClient.invalidateQueries({ queryKey: ['projects'] });
            queryClient.invalidateQueries({ queryKey: ['projects', variables.projectId] });
            toast.success('Project updated successfully');
        },
        onError: (error: any) => {
            const message = error.response?.data?.message ||
                error.response?.data?.detail ||
                'Failed to update project';
            toast.error(message);
        },
    });

    return {
        updateProject: mutation.mutateAsync,
        isUpdating: mutation.isPending,
        error: mutation.error,
    };
}

/**
 * Hook to delete a project
 * 
 * @example
 * const { deleteProject, isDeleting } = useDeleteProject();
 * await deleteProject(projectId);
 */
export function useDeleteProject() {
    const queryClient = useQueryClient();

    const mutation = useMutation({
        mutationFn: async (projectId: string) => {
            const response = await projectAPI.deleteProject(projectId);
            return response.data;
        },
        onSuccess: () => {
            // Invalidate projects list
            queryClient.invalidateQueries({ queryKey: ['projects'] });
            toast.success('Project deleted successfully');
        },
        onError: (error: any) => {
            const message = error.response?.data?.message ||
                error.response?.data?.detail ||
                'Failed to delete project';
            toast.error(message);
        },
    });

    return {
        deleteProject: mutation.mutateAsync,
        isDeleting: mutation.isPending,
        error: mutation.error,
    };
}

/**
 * Hook to fetch layers for a specific project
 * 
 * @param projectId - ID of the project
 * @example
 * const { layers, isLoading } = useProjectLayers(projectId);
 */
export function useProjectLayers(projectId: string | undefined) {
    const { data, isLoading, error } = useQuery({
        queryKey: ['projects', projectId, 'layers'],
        queryFn: async () => {
            if (!projectId) throw new Error('Project ID is required');
            const response = await projectAPI.getProjectLayers(projectId);
            return response.data;
        },
        enabled: !!projectId,
    });

    return {
        layers: data || [],
        isLoading,
        error,
    };
}

/**
 * Hook to assign a layer to a project
 * 
 * @example
 * const { assignLayer, isAssigning } = useAssignLayer();
 * await assignLayer({ projectId: '123', layerId: '456' });
 */
export function useAssignLayer() {
    const queryClient = useQueryClient();

    const mutation = useMutation({
        mutationFn: async ({ projectId, layerId }: { projectId: string; layerId: string }) => {
            const response = await projectAPI.assignLayer(projectId, layerId);
            return response.data;
        },
        onSuccess: (_data, variables) => {
            // Invalidate project layers
            queryClient.invalidateQueries({ queryKey: ['projects', variables.projectId, 'layers'] });
            toast.success('Layer assigned to project');
        },
        onError: (error: any) => {
            const message = error.response?.data?.message ||
                error.response?.data?.detail ||
                'Failed to assign layer';
            toast.error(message);
        },
    });

    return {
        assignLayer: mutation.mutateAsync,
        isAssigning: mutation.isPending,
        error: mutation.error,
    };
}

/**
 * Hook to remove a layer from a project
 * 
 * @example
 * const { removeLayer, isRemoving } = useRemoveLayer();
 * await removeLayer({ projectId: '123', layerId: '456' });
 */
export function useRemoveLayer() {
    const queryClient = useQueryClient();

    const mutation = useMutation({
        mutationFn: async ({ projectId, layerId }: { projectId: string; layerId: string }) => {
            const response = await projectAPI.removeLayer(projectId, layerId);
            return response.data;
        },
        onSuccess: (_data, variables) => {
            // Invalidate project layers
            queryClient.invalidateQueries({ queryKey: ['projects', variables.projectId, 'layers'] });
            toast.success('Layer removed from project');
        },
        onError: (error: any) => {
            const message = error.response?.data?.message ||
                error.response?.data?.detail ||
                'Failed to remove layer';
            toast.error(message);
        },
    });

    return {
        removeLayer: mutation.mutateAsync,
        isRemoving: mutation.isPending,
        error: mutation.error,
    };
}
