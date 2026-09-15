export const mockProjects = [
    {
        id: "mock-project-1",
        name: "Urban Planning Project",
        workspace_id: "mock-workspace-1",
        description: "City infrastructure mapping and analysis",
        layer_count: 12,
        status: "active",
        created_at: "2024-03-01T00:00:00Z",
        updated_at: "2024-03-10T00:00:00Z"
    },
    {
        id: "mock-project-2",
        name: "Environmental Analysis",
        workspace_id: "mock-workspace-1",
        description: "Forest coverage and environmental impact study",
        layer_count: 8,
        status: "active",
        created_at: "2024-03-15T00:00:00Z",
        updated_at: "2024-03-20T00:00:00Z"
    },
    {
        id: "mock-project-3",
        name: "Property Development",
        workspace_id: "mock-workspace-2",
        description: "Real estate development planning",
        layer_count: 15,
        status: "active",
        created_at: "2024-02-20T00:00:00Z",
        updated_at: "2024-03-05T00:00:00Z"
    },
    {
        id: "mock-project-4",
        name: "Transportation Network",
        workspace_id: "mock-workspace-1",
        description: "Road and public transport analysis",
        layer_count: 6,
        status: "archived",
        created_at: "2024-01-10T00:00:00Z",
        updated_at: "2024-02-01T00:00:00Z"
    }
];

// Track layer assignments
const projectLayerAssignments: Record<string, string[]> = {
    "mock-project-1": ["layer-1", "layer-2", "layer-3"],
    "mock-project-2": ["layer-4", "layer-5"],
    "mock-project-3": ["layer-1", "layer-6", "layer-7"],
};

const delay = (ms: number = 500) => new Promise(resolve => setTimeout(resolve, ms));

export const getProjects = async (workspaceId?: string) => {
    await delay();

    if (workspaceId) {
        const filtered = mockProjects.filter(p => p.workspace_id === workspaceId);
        return { data: filtered };
    }

    return { data: mockProjects };
};

export const getProjectById = async (id: string) => {
    await delay();
    const project = mockProjects.find(p => p.id === id);

    if (!project) {
        throw new Error(`Project ${id} not found`);
    }

    return { data: project };
};

export const createProject = async (data: { name: string; description?: string; workspace_id?: string }) => {
    await delay();

    const newProject = {
        id: `mock-project-${Date.now()}`,
        name: data.name,
        description: data.description || "",
        workspace_id: data.workspace_id || "mock-workspace-1",
        layer_count: 0,
        status: "active",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
    };

    mockProjects.push(newProject);
    projectLayerAssignments[newProject.id] = [];

    return { data: newProject };
};

export const updateProject = async (id: string, data: { name?: string; description?: string }) => {
    await delay();
    const index = mockProjects.findIndex(p => p.id === id);

    if (index === -1) {
        throw new Error(`Project ${id} not found`);
    }

    mockProjects[index] = {
        ...mockProjects[index],
        ...data,
        updated_at: new Date().toISOString()
    };

    return { data: mockProjects[index] };
};

export const deleteProject = async (id: string) => {
    await delay();
    const index = mockProjects.findIndex(p => p.id === id);

    if (index === -1) {
        throw new Error(`Project ${id} not found`);
    }

    mockProjects.splice(index, 1);
    delete projectLayerAssignments[id];

    return { data: { message: "Project deleted successfully" } };
};

export const getProjectLayers = async (projectId: string) => {
    await delay();
    const layerIds = projectLayerAssignments[projectId] || [];

    // Import layers to get layer data
    const layersModule = await import('./layers');
    const layers = layersModule.mockLayers.filter((l: any) => layerIds.includes(l.id));

    return { data: layers };
};

export const assignLayer = async (projectId: string, layerId: string) => {
    await delay();

    if (!projectLayerAssignments[projectId]) {
        projectLayerAssignments[projectId] = [];
    }

    if (!projectLayerAssignments[projectId].includes(layerId)) {
        projectLayerAssignments[projectId].push(layerId);

        // Update layer count
        const project = mockProjects.find(p => p.id === projectId);
        if (project) {
            project.layer_count = projectLayerAssignments[projectId].length;
        }
    }

    return { data: { message: "Layer assigned successfully" } };
};

export const removeLayer = async (projectId: string, layerId: string) => {
    await delay();

    if (projectLayerAssignments[projectId]) {
        projectLayerAssignments[projectId] = projectLayerAssignments[projectId].filter(id => id !== layerId);

        // Update layer count
        const project = mockProjects.find(p => p.id === projectId);
        if (project) {
            project.layer_count = projectLayerAssignments[projectId].length;
        }
    }

    return { data: { message: "Layer removed successfully" } };
};
