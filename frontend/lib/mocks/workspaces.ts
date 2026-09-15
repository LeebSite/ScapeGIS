export const mockWorkspaces = [
    {
        id: "mock-workspace-1",
        name: "My Development Workspace",
        description: "Main workspace for development projects",
        role: "owner",
        subscription_name: "Professional",
        member_count: 3,
        project_count: 5,
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-15T00:00:00Z"
    },
    {
        id: "mock-workspace-2",
        name: "Team Collaboration",
        description: "Shared workspace for team projects",
        role: "member",
        subscription_name: "Basic",
        member_count: 8,
        project_count: 12,
        created_at: "2024-02-15T00:00:00Z",
        updated_at: "2024-03-01T00:00:00Z"
    },
    {
        id: "mock-workspace-3",
        name: "GIS Research Lab",
        description: "Academic research and analysis",
        role: "admin",
        subscription_name: "Professional",
        member_count: 5,
        project_count: 8,
        created_at: "2024-03-10T00:00:00Z",
        updated_at: "2024-03-20T00:00:00Z"
    }
];

export const mockWorkspaceDetail = {
    id: "mock-workspace-1",
    name: "My Development Workspace",
    description: "Main workspace for development projects",
    owner: {
        id: "user-1",
        name: "Current User",
        email: "user@example.com"
    },
    subscription: {
        name: "Professional",
        max_projects: 50,
        max_members: 20,
        features: ["Advanced GIS", "AI Analysis", "Team Collaboration"]
    },
    members: [
        { id: "1", name: "John Doe", email: "john@example.com", role: "admin" },
        { id: "2", name: "Jane Smith", email: "jane@example.com", role: "member" },
        { id: "3", name: "Bob Johnson", email: "bob@example.com", role: "viewer" }
    ],
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-15T00:00:00Z"
};

// Simulate network delay
const delay = (ms: number = 500) => new Promise(resolve => setTimeout(resolve, ms));

// Mock API functions
export const getWorkspaces = async () => {
    await delay();
    return { data: mockWorkspaces };
};

export const getWorkspaceById = async (id: string) => {
    await delay();
    const workspace = mockWorkspaces.find(w => w.id === id);
    if (!workspace) {
        throw new Error(`Workspace ${id} not found`);
    }
    return { data: mockWorkspaceDetail };
};

export const createWorkspace = async (data: { name: string; description?: string }) => {
    await delay();
    const newWorkspace = {
        id: `mock-workspace-${Date.now()}`,
        name: data.name,
        description: data.description || "",
        role: "owner",
        subscription_name: "Free",
        member_count: 1,
        project_count: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
    };

    mockWorkspaces.push(newWorkspace);
    return { data: newWorkspace };
};

export const updateWorkspace = async (id: string, data: { name?: string; description?: string }) => {
    await delay();
    const index = mockWorkspaces.findIndex(w => w.id === id);

    if (index === -1) {
        throw new Error(`Workspace ${id} not found`);
    }

    mockWorkspaces[index] = {
        ...mockWorkspaces[index],
        ...data,
        updated_at: new Date().toISOString()
    };

    return { data: mockWorkspaces[index] };
};

export const deleteWorkspace = async (id: string) => {
    await delay();
    const index = mockWorkspaces.findIndex(w => w.id === id);

    if (index === -1) {
        throw new Error(`Workspace ${id} not found`);
    }

    mockWorkspaces.splice(index, 1);
    return { data: { message: "Workspace deleted successfully" } };
};
