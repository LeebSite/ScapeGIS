/**
 * GIS Service - API calls for GIS data management
 */

import http from './http';
import type {
    GISDataset,
    GISLayer,
    GeoJSONFeatureCollection,
    UploadProgress
} from '@/lib/types/gis';

const GIS_BASE_PATH = '/gis';

export const GISService = {
    /**
     * Upload GIS file (ZIP containing GeoJSON, Shapefile, KML, or GeoPackage)
     */
    async uploadGISFile(
        file: File,
        name: string,
        description?: string,
        isPublic?: boolean,
        onProgress?: (percent: number) => void
    ): Promise<GISDataset> {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('name', name);
        if (description) {
            formData.append('description', description);
        }
        formData.append('is_public', String(isPublic || false));

        const response = await http.post<GISDataset>(
            `${GIS_BASE_PATH}/upload`,
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                onUploadProgress: (progressEvent: any) => {
                    if (onProgress && progressEvent.total) {
                        const percentCompleted = Math.round(
                            (progressEvent.loaded * 100) / progressEvent.total
                        );
                        onProgress(percentCompleted);
                    }
                },
            }
        );

        return response.data;
    },

    /**
     * Get all datasets for the current user
     */
    async getDatasets(skip: number = 0, limit: number = 100): Promise<GISDataset[]> {
        const response = await http.get<GISDataset[]>(`${GIS_BASE_PATH}/datasets`, {
            params: { skip, limit },
        });
        return response.data;
    },

    /**
     * Get a single dataset by ID
     */
    async getDataset(datasetId: string): Promise<GISDataset> {
        const response = await http.get<GISDataset>(
            `${GIS_BASE_PATH}/datasets/${datasetId}`
        );
        return response.data;
    },

    /**
     * Delete a dataset
     */
    async deleteDataset(datasetId: string): Promise<void> {
        await http.delete(`${GIS_BASE_PATH}/datasets/${datasetId}`);
    },

    /**
     * Get layers for a dataset
     */
    async getDatasetLayers(datasetId: string): Promise<GISLayer[]> {
        const response = await http.get<GISLayer[]>(
            `${GIS_BASE_PATH}/datasets/${datasetId}/layers`
        );
        return response.data;
    },

    /**
     * Get GeoJSON data for a specific layer (for map preview)
     */
    async getLayerGeoJSON(layerId: string): Promise<GeoJSONFeatureCollection> {
        const response = await http.get<GeoJSONFeatureCollection>(
            `${GIS_BASE_PATH}/layers/${layerId}/geojson`
        );
        return response.data;
    },

    /**
     * Update layer visibility
     */
    async updateLayerVisibility(layerId: string, isVisible: boolean): Promise<GISLayer> {
        const response = await http.patch<GISLayer>(
            `${GIS_BASE_PATH}/layers/${layerId}`,
            { is_visible: isVisible }
        );
        return response.data;
    },
};

export default GISService;
