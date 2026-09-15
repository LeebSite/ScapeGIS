import http from "./http";
import type { Layer } from "../types";
import { API_CONFIG } from "./config";
import * as mockLayer from "@/lib/mocks/layers";

export interface LayerFilters {
    region?: string;
    type?: "vector" | "raster";
    subscription_level?: "free" | "basic" | "professional";
}

export const layerAPI = {
    /**
     * Get all available layers (filtered by user subscription level)
     * GET /layers
     * 
     * Backend automatically filters based on user's subscription.
     * Free users see only free layers, Basic sees free + basic, etc.
     * 
     * @param filters - Optional filters for region, type, subscription level
     * @returns Array of available layers for current user
     */
    getAvailableLayers: (filters?: LayerFilters) =>
        http.get<Layer[]>("/layers", { params: filters }),

    /**
     * Get layer details by ID
     * GET /layers/{id}
     * 
     * Requires permission: layers.read
     * Users can only access layers within their subscription level
     * 
     * @param layerId - Unique layer identifier
     * @returns Layer details
     */
    getLayerById: (layerId: string) =>
        http.get<Layer>(`/layers/${layerId}`),

    /**
     * Search layers by name or description
     * GET /layers/search
     * 
     * @param query - Search term
     * @returns Matching layers within user's subscription
     */
    searchLayers: (query: string) =>
        http.get<Layer[]>("/layers/search", { params: { q: query } }),
};
