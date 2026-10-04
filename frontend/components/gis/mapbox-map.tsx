"use client";

import { useEffect, useState, useMemo } from 'react';
import Map, { Source, Layer, NavigationControl, Marker } from 'react-map-gl/maplibre';
import type { GeoJSONFeatureCollection } from '@/lib/types/gis';
import 'mapbox-gl/dist/mapbox-gl.css';

export interface MapboxMapProps {
    geojson?: GeoJSONFeatureCollection | null;
    selectedLocation?: { latitude: number; longitude: number } | null;
    onMapClick?: (coords: { latitude: number; longitude: number }) => void;
    highlightFeatures?: GeoJSONFeatureCollection | null;
    height?: string;
}

export default function MapboxMap({
    geojson,
    selectedLocation,
    onMapClick,
    highlightFeatures,
    height = '600px',
}: MapboxMapProps) {
    const [viewState, setViewState] = useState({
        longitude: 101.4478,
        latitude: 0.5071,
        zoom: 12
    });

    // Auto-fit bounds when geojson loads with features
    useEffect(() => {
        if (geojson && geojson.features && geojson.features.length > 0) {
            try {
                let minLng = Infinity, minLat = Infinity;
                let maxLng = -Infinity, maxLat = -Infinity;

                geojson.features.forEach(feature => {
                    const coords = getCoordinates(feature.geometry);
                    coords.forEach(([lng, lat]) => {
                        minLng = Math.min(minLng, lng);
                        minLat = Math.min(minLat, lat);
                        maxLng = Math.max(maxLng, lng);
                        maxLat = Math.max(maxLat, lat);
                    });
                });

                if (isFinite(minLng) && isFinite(maxLng)) {
                    const centerLng = (minLng + maxLng) / 2;
                    const centerLat = (minLat + maxLat) / 2;

                    setViewState({
                        longitude: centerLng,
                        latitude: centerLat,
                        zoom: calculateZoom(minLng, minLat, maxLng, maxLat)
                    });
                }
            } catch (err) {
                console.error('Failed to fit bounds:', err);
            }
        }
    }, [geojson]);

    return (
        <Map
            {...viewState}
            onMove={(evt: any) => setViewState(evt.viewState)}
            onClick={(evt: any) => {
                if (onMapClick && evt.lngLat) {
                    onMapClick({
                        latitude: Number(evt.lngLat.lat.toFixed(6)),
                        longitude: Number(evt.lngLat.lng.toFixed(6)),
                    });
                }
            }}
            cursor={onMapClick ? 'crosshair' : 'grab'}
            style={{ width: '100%', height }}
            mapStyle={{
                version: 8,
                sources: {
                    'osm-tiles': {
                        type: 'raster',
                        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
                        tileSize: 256,
                        attribution: '&copy; OpenStreetMap Contributors'
                    }
                },
                layers: [
                    {
                        id: 'osm-tiles',
                        type: 'raster',
                        source: 'osm-tiles',
                        minzoom: 0,
                        maxzoom: 19
                    }
                ]
            }}
        >
            <NavigationControl position="top-right" />

            {/* Selected Location Marker */}
            {selectedLocation && (
                <Marker
                    longitude={selectedLocation.longitude}
                    latitude={selectedLocation.latitude}
                    anchor="bottom"
                >
                    <div className="flex flex-col items-center pointer-events-none">
                        <div className="bg-red-600 text-white text-[10px] font-bold px-2 py-0.5 rounded shadow-lg whitespace-nowrap mb-1">
                            Titik Target ({selectedLocation.latitude.toFixed(4)}, {selectedLocation.longitude.toFixed(4)})
                        </div>
                        <div className="relative flex items-center justify-center">
                            <span className="animate-ping absolute inline-flex h-5 w-5 rounded-full bg-red-400 opacity-75"></span>
                            <div className="w-5 h-5 bg-red-600 border-2 border-white rounded-full shadow-md flex items-center justify-center">
                                <div className="w-1.5 h-1.5 bg-white rounded-full" />
                            </div>
                        </div>
                    </div>
                </Marker>
            )}

            {/* Highlight Features (Spatial Analysis results) */}
            {highlightFeatures && highlightFeatures.features && highlightFeatures.features.length > 0 && (
                <Source id="highlight-data" type="geojson" data={highlightFeatures as any}>
                    <Layer
                        id="highlight-polygon"
                        type="fill"
                        filter={['==', ['geometry-type'], 'Polygon']}
                        paint={{
                            'fill-color': '#8b5cf6',
                            'fill-opacity': 0.35
                        }}
                    />
                    <Layer
                        id="highlight-polygon-line"
                        type="line"
                        filter={['==', ['geometry-type'], 'Polygon']}
                        paint={{
                            'line-color': '#7c3aed',
                            'line-width': 2.5
                        }}
                    />
                    <Layer
                        id="highlight-line"
                        type="line"
                        filter={['==', ['geometry-type'], 'LineString']}
                        paint={{
                            'line-color': '#f59e0b',
                            'line-width': 4
                        }}
                    />
                    <Layer
                        id="highlight-point"
                        type="circle"
                        filter={['==', ['geometry-type'], 'Point']}
                        paint={{
                            'circle-color': '#10b981',
                            'circle-radius': 9,
                            'circle-stroke-width': 3,
                            'circle-stroke-color': '#ffffff'
                        }}
                    />
                </Source>
            )}

            {/* Main Project GIS Data */}
            {geojson && geojson.features && geojson.features.length > 0 && (
                <Source id="gis-data" type="geojson" data={geojson as any}>
                    {/* Fill layer for polygons */}
                    <Layer
                        id="polygon-fill"
                        type="fill"
                        filter={['==', ['geometry-type'], 'Polygon']}
                        paint={{
                            'fill-color': '#3b82f6',
                            'fill-opacity': 0.3
                        }}
                    />

                    {/* Outline layer for polygons */}
                    <Layer
                        id="polygon-outline"
                        type="line"
                        filter={['==', ['geometry-type'], 'Polygon']}
                        paint={{
                            'line-color': '#3b82f6',
                            'line-width': 2
                        }}
                    />

                    {/* Line layer */}
                    <Layer
                        id="line"
                        type="line"
                        filter={['==', ['geometry-type'], 'LineString']}
                        paint={{
                            'line-color': '#3b82f6',
                            'line-width': 3
                        }}
                    />

                    {/* Point layer */}
                    <Layer
                        id="point"
                        type="circle"
                        filter={['==', ['geometry-type'], 'Point']}
                        paint={{
                            'circle-color': '#ef4444',
                            'circle-radius': 8,
                            'circle-stroke-width': 2,
                            'circle-stroke-color': '#ffffff'
                        }}
                    />
                </Source>
            )}
        </Map>
    );
}

// Helper function to extract coordinates from geometry
function getCoordinates(geometry: any): number[][] {
    const coords: number[][] = [];
    if (!geometry) return coords;

    if (geometry.type === 'Point') {
        coords.push(geometry.coordinates);
    } else if (geometry.type === 'LineString') {
        coords.push(...geometry.coordinates);
    } else if (geometry.type === 'Polygon') {
        coords.push(...geometry.coordinates[0]);
    } else if (geometry.type === 'MultiPoint') {
        coords.push(...geometry.coordinates);
    } else if (geometry.type === 'MultiLineString') {
        geometry.coordinates.forEach((line: number[][]) => coords.push(...line));
    } else if (geometry.type === 'MultiPolygon') {
        geometry.coordinates.forEach((polygon: number[][][]) => coords.push(...polygon[0]));
    }

    return coords;
}

// Calculate appropriate zoom level based on bounds
function calculateZoom(minLng: number, minLat: number, maxLng: number, maxLat: number): number {
    const lngDiff = maxLng - minLng;
    const latDiff = maxLat - minLat;
    const maxDiff = Math.max(lngDiff, latDiff);

    if (maxDiff > 10) return 5;
    if (maxDiff > 5) return 7;
    if (maxDiff > 1) return 9;
    if (maxDiff > 0.5) return 11;
    if (maxDiff > 0.1) return 13;
    return 15;
}