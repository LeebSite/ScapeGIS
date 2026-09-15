/**
 * GIS Data Types
 * Interface untuk GIS Datasets, Layers, dan GeoJSON
 */

export type FileType = 'geojson' | 'shapefile' | 'kml' | 'geopackage';
export type DatasetStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type GeometryType = 'Point' | 'LineString' | 'Polygon' | 'MultiPoint' | 'MultiLineString' | 'MultiPolygon' | 'GeometryCollection';

export interface GISLayer {
    id: string;                    // UUID
    dataset_id: string;
    name: string;
    description: string | null;
    geometry_type: GeometryType | null;
    feature_count: number;
    bbox: number[] | null;         // [minx, miny, maxx, maxy]
    crs: string | null;            // Always 'EPSG:4326'
    geojson_data: any | null;      // Preview GeoJSON
    style: any | null;
    is_visible: boolean;
    layer_order: number;
    created_at: string;            // ISO datetime
    updated_at: string;            // ISO datetime
}

export interface GISDataset {
    id: string;                    // UUID
    user_id: string;               // UUID
    name: string;
    description: string | null;
    original_filename: string;
    file_type: FileType;
    file_size: number | null;
    source?: string | null;        // e.g., 'upload'
    bbox: number[] | null;         // [minx, miny, maxx, maxy]
    crs: string | null;            // Original CRS
    srid?: number | null;          // Target SRID (always 4326)
    geometry_type?: string | null; // Dominant geometry type
    total_layers?: number;         // Total number of layers
    total_features?: number;       // Total number of features
    status: DatasetStatus;
    error_message: string | null;
    is_public: boolean;
    created_at: string;            // ISO datetime
    updated_at: string;            // ISO datetime
    layers?: GISLayer[];           // Optional, may not be included in list response
}

export interface GeoJSONFeature {
    type: 'Feature';
    geometry: {
        type: GeometryType;
        coordinates: any;
    };
    properties: Record<string, any>;
    id?: string | number;
}

export interface GeoJSONFeatureCollection {
    type: 'FeatureCollection';
    features: GeoJSONFeature[];
    bbox?: number[];
}

export interface UploadGISRequest {
    file: File;
    name: string;
    description?: string;
    is_public?: boolean;
}

export interface UploadProgress {
    percent: number;
    loaded: number;
    total: number;
}
