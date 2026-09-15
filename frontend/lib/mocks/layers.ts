export const mockLayers = [
    {
        id: "layer-1",
        name: "Building Footprints",
        type: "vector" as const,
        region: "Jakarta",
        subscription_level: "free" as const,
        feature_count: 1543,
        file_size_mb: 12.5,
        description: "Building footprints for Jakarta area",
        visible: true,
        created_at: "2024-01-15T00:00:00Z"
    },
    {
        id: "layer-2",
        name: "Road Network",
        type: "vector" as const,
        region: "Jakarta",
        subscription_level: "free" as const,
        feature_count: 892,
        file_size_mb: 8.3,
        description: "Complete road network data",
        visible: true,
        created_at: "2024-01-20T00:00:00Z"
    },
    {
        id: "layer-3",
        name: "Points of Interest",
        type: "vector" as const,
        region: "Jakarta",
        subscription_level: "basic" as const,
        feature_count: 234,
        file_size_mb: 2.1,
        description: "Commercial and public facilities",
        visible: false,
        created_at: "2024-02-01T00:00:00Z"
    },
    {
        id: "layer-4",
        name: "Land Use Classification",
        type: "raster" as const,
        region: "Jakarta",
        subscription_level: "professional" as const,
        feature_count: 0,
        file_size_mb: 45.2,
        description: "Detailed land use classification raster",
        visible: true,
        created_at: "2024-02-10T00:00:00Z"
    },
    {
        id: "layer-5",
        name: "Elevation Model (DEM)",
        type: "raster" as const,
        region: "All Regions",
        subscription_level: "professional" as const,
        feature_count: 0,
        file_size_mb: 120.7,
        description: "Digital elevation model for terrain analysis",
        visible: true,
        created_at: "2024-02-15T00:00:00Z"
    },
    {
        id: "layer-6",
        name: "Property Boundaries",
        type: "vector" as const,
        region: "Bandung",
        subscription_level: "basic" as const,
        feature_count: 567,
        file_size_mb: 6.8,
        description: "Property cadastral boundaries",
        visible: true,
        created_at: "2024-03-01T00:00:00Z"
    },
    {
        id: "layer-7",
        name: "Flood Risk Zones",
        type: "vector" as const,
        region: "All Regions",
        subscription_level: "professional" as const,
        feature_count: 145,
        file_size_mb: 15.3,
        description: "Flood hazard risk assessment zones",
        visible: false,
        created_at: "2024-03-05T00:00:00Z"
    },
    {
        id: "layer-8",
        name: "Satellite Imagery",
        type: "raster" as const,
        region: "Surabaya",
        subscription_level: "free" as const,
        feature_count: 0,
        file_size_mb: 89.4,
        description: "Recent satellite imagery basemap",
        visible: true,
        created_at: "2024-03-10T00:00:00Z"
    }
];

const delay = (ms: number = 300) => new Promise(resolve => setTimeout(resolve, ms));

export interface LayerFilters {
    region?: string;
    type?: "vector" | "raster";
    subscription_level?: "free" | "basic" | "professional";
}

export const getLayers = async (filters?: LayerFilters) => {
    await delay();

    let filtered = [...mockLayers];

    if (filters?.region && filters.region !== 'All Regions') {
        filtered = filtered.filter(l =>
            l.region === filters.region || l.region === 'All Regions'
        );
    }

    if (filters?.type) {
        filtered = filtered.filter(l => l.type === filters.type);
    }

    if (filters?.subscription_level) {
        // Filter by subscription hierarchy: free < basic < professional
        const hierarchy: Record<string, number> = {
            free: 1,
            basic: 2,
            professional: 3
        };

        const userLevel = hierarchy[filters.subscription_level];
        filtered = filtered.filter(l => hierarchy[l.subscription_level] <= userLevel);
    }

    return { data: filtered };
};

export const getLayerById = async (layerId: string) => {
    await delay();
    const layer = mockLayers.find(l => l.id === layerId);

    if (!layer) {
        throw new Error(`Layer ${layerId} not found`);
    }

    return { data: layer };
};

export const searchLayers = async (query: string) => {
    await delay();

    if (!query || query.trim() === '') {
        return { data: [] };
    }

    const lowerQuery = query.toLowerCase();
    const results = mockLayers.filter(l =>
        l.name.toLowerCase().includes(lowerQuery) ||
        l.description.toLowerCase().includes(lowerQuery) ||
        l.region.toLowerCase().includes(lowerQuery)
    );

    return { data: results };
};
