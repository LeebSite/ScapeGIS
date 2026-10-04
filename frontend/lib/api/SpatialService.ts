// Spatial API client
import http from "./http";

export interface LayerSemanticResponse {
    id: string;
    layer_id: string;
    category: string;
    subcategory: string;
    display_name: string;
    description?: string;
    ai_enabled: boolean;
    semantic_metadata?: Record<string, any>;
    layer_name?: string;
    geometry_type?: string;
    feature_count?: number;
    created_at: string;
    updated_at: string;
}

export interface NearestRequest {
    latitude: number;
    longitude: number;
    subcategory: string;
    workspace_id: string;
}

export interface RadiusRequest {
    latitude: number;
    longitude: number;
    subcategory: string;
    radius_meters?: number;
    workspace_id: string;
}

export interface SpatialContextRequest {
    latitude: number;
    longitude: number;
    workspace_id: string;
    project_id?: string;
}

export interface ContainmentRequest {
    latitude: number;
    longitude: number;
    layer_id: string;
    workspace_id: string;
}

export interface IntersectionRequest {
    latitude: number;
    longitude: number;
    layer_id: string;
    workspace_id: string;
    buffer_meters?: number;
}

export interface NearestFeatureResult {
    feature_id: string;
    distance_meters: number;
    properties: Record<string, any>;
    layer_id?: string;
    layer_name?: string;
    display_name?: string;
    subcategory?: string;
}

export interface RadiusFeature {
    feature_id: string;
    distance_meters: number;
    properties: Record<string, any>;
    layer_id?: string;
    display_name?: string;
}

export interface RadiusSearchResult {
    latitude: number;
    longitude: number;
    subcategory: string;
    radius_meters: number;
    count: number;
    features: RadiusFeature[];
}

export interface ContainmentResult {
    feature_id: string;
    properties: Record<string, any>;
}

export interface SpatialFactItem {
    type: string;
    category: string;
    subcategory: string;
    display_name?: string;
    layer_id?: string;
    distance_meters?: number;
    count_within_2km?: number;
    count_within_1km?: number;
    area_name?: string;
    properties?: Record<string, any>;
}

export interface SpatialContextResponse {
    location: { latitude: number; longitude: number };
    workspace_id: string;
    project_id?: string;
    project?: Record<string, any>;
    authorized_datasets: string[];
    transportation: Record<string, any>;
    facilities: Record<string, any>;
    religious: Record<string, any>;
    administrative: Record<string, any>;
    facts: SpatialFactItem[];
    warning?: string;
}

export interface SemanticSeedResponse {
    created: number;
    updated: number;
    skipped: number;
    total_catalog_entries: number;
    message: string;
}

export const SpatialService = {
    /**
     * Get semantic layers authorized for workspace
     */
    async getSemanticLayers(workspaceId: string): Promise<LayerSemanticResponse[]> {
        const res = await http.get<LayerSemanticResponse[]>("/spatial/layers", {
            params: { workspace_id: workspaceId },
        });
        return res.data;
    },

    /**
     * Find nearest feature of a given semantic subcategory
     */
    async findNearest(payload: NearestRequest): Promise<NearestFeatureResult> {
        const res = await http.post<NearestFeatureResult>("/spatial/nearest", payload);
        return res.data;
    },

    /**
     * Search features within radius for a semantic subcategory
     */
    async radiusSearch(payload: RadiusRequest): Promise<RadiusSearchResult> {
        const res = await http.post<RadiusSearchResult>("/spatial/radius", payload);
        return res.data;
    },

    /**
     * Build comprehensive spatial context for a coordinate
     */
    async getSpatialContext(payload: SpatialContextRequest): Promise<SpatialContextResponse> {
        const res = await http.post<SpatialContextResponse>("/spatial/context", payload);
        return res.data;
    },

    /**
     * Check which polygon feature contains the coordinate
     */
    async checkContainment(payload: ContainmentRequest): Promise<ContainmentResult | null> {
        const res = await http.post<ContainmentResult | null>("/spatial/containment", payload);
        return res.data;
    },

    /**
     * Check features intersecting buffer around coordinate
     */
    async checkIntersection(payload: IntersectionRequest): Promise<any> {
        const res = await http.post<any>("/spatial/intersection", payload);
        return res.data;
    },

    /**
     * Admin: Seed default GIS semantics
     */
    async seedSemantics(): Promise<SemanticSeedResponse> {
        const res = await http.post<SemanticSeedResponse>("/spatial/admin/seed-semantics");
        return res.data;
    },
};

export default SpatialService;