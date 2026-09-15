import { useQuery } from '@tanstack/react-query';
import { layerAPI, LayerFilters } from '@/lib/api/LayerService';
import type { Layer } from '@/lib/types';
import { useAuthStore } from '@/lib/store';

/**
 * Hook to fetch all available layers for current user
 * Automatically filtered by user's subscription level
 * 
 * @param filters - Optional filters for region, type, subscription level
 * @example
 * const { layers, isLoading } = useLayers();
 * const { layers } = useLayers({ region: 'Jakarta', type: 'vector' });
 */
export function useLayers(filters?: LayerFilters) {
    const { user } = useAuthStore();

    const { data, isLoading, error, refetch } = useQuery({
        queryKey: ['layers', filters],
        queryFn: async () => {
            const response = await layerAPI.getAvailableLayers(filters);
            return response.data;
        },
        enabled: !!user, // Only fetch if user is logged in
    });

    return {
        layers: data || [],
        isLoading,
        error,
        refetch,
    };
}

/**
 * Hook to fetch a single layer by ID
 * 
 * @param layerId - ID of the layer to fetch
 * @example
 * const { layer, isLoading } = useLayer(layerId);
 */
export function useLayer(layerId: string | undefined) {
    const { data, isLoading, error } = useQuery({
        queryKey: ['layers', layerId],
        queryFn: async () => {
            if (!layerId) throw new Error('Layer ID is required');
            const response = await layerAPI.getLayerById(layerId);
            return response.data;
        },
        enabled: !!layerId,
    });

    return {
        layer: data,
        isLoading,
        error,
    };
}

/**
 * Hook to search layers by query string
 * 
 * @param query - Search query
 * @param enabled - Whether to enable the search (default: true when query is not empty)
 * @example
 * const { layers, isSearching } = useSearchLayers(searchTerm);
 */
export function useSearchLayers(query: string, enabled = true) {
    const { data, isLoading, error } = useQuery({
        queryKey: ['layers', 'search', query],
        queryFn: async () => {
            const response = await layerAPI.searchLayers(query);
            return response.data;
        },
        enabled: enabled && query.length > 0, // Only search if query is not empty
        staleTime: 30000, // Cache results for 30 seconds
    });

    return {
        layers: data || [],
        isSearching: isLoading,
        error,
    };
}

/**
 * Hook to get layers filtered by subscription level
 * Useful for showing what layers are available in different subscription tiers
 * 
 * @param subscriptionLevel - Subscription level to filter by
 * @example
 * const { layers } = useLayersBySubscription('professional');
 */
export function useLayersBySubscription(
    subscriptionLevel: 'free' | 'basic' | 'professional'
) {
    return useLayers({ subscription_level: subscriptionLevel });
}

/**
 * Hook to get layers by region
 * 
 * @param region - Region name to filter by
 * @example
 * const { layers } = useLayersByRegion('Jakarta');
 */
export function useLayersByRegion(region: string) {
    return useLayers({ region });
}

/**
 * Hook to get layers by type
 * 
 * @param type - Layer type (vector or raster)
 * @example
 * const { layers } = useLayersByType('vector');
 */
export function useLayersByType(type: 'vector' | 'raster') {
    return useLayers({ type });
}
