"use client";

import { useEffect, useState } from 'react';
import Map, { Source, Layer, NavigationControl } from 'react-map-gl/maplibre';
import type { GeoJSONFeatureCollection } from '@/lib/types/gis';
import 'mapbox-gl/dist/mapbox-gl.css';

interface MapboxMapProps {
    geojson: GeoJSONFeatureCollection | null;
}

// 🔑 GANTI INI DENGAN TOKEN MAPBOX ANDA!
// Daftar gratis di: https://account.mapbox.com/auth/signup/
const MAPBOX_TOKEN = 'YOUR_MAPBOX_TOKEN_HERE';

export default function MapboxMapStyled({ geojson }: MapboxMapProps) {
    const [viewState, setViewState] = useState({
        longitude: 101.4478,
        latitude: 0.5071,
        zoom: 12
    });

    // Auto-fit bounds when geojson loads
    useEffect(() => {
        if (geojson && geojson.features.length > 0) {
            try {
                // Calculate bounds from features
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

                // Calculate center and zoom
                const centerLng = (minLng + maxLng) / 2;
                const centerLat = (minLat + maxLat) / 2;

                setViewState({
                    longitude: centerLng,
                    latitude: centerLat,
                    zoom: calculateZoom(minLng, minLat, maxLng, maxLat)
                });
            } catch (err) {
                console.error('Failed to fit bounds:', err);
            }
        }
    }, [geojson]);

    if (!geojson) return null;

    return (
        <Map
            {...viewState}
            onMove={(evt: any) => setViewState(evt.viewState)}
            style={{ width: '100%', height: '600px' }}
            // 🎨 PILIHAN STYLE MAPBOX (uncomment salah satu):

            // Option 1: Streets (Default - Clean & Modern)
            mapStyle={`https://api.mapbox.com/styles/v1/mapbox/streets-v12?access_token=${MAPBOX_TOKEN}`}

        // Option 2: Satellite (Imagery)
        // mapStyle={`https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12?access_token=${MAPBOX_TOKEN}`}

        // Option 3: Dark Mode (Modern Dark Theme)
        // mapStyle={`https://api.mapbox.com/styles/v1/mapbox/dark-v11?access_token=${MAPBOX_TOKEN}`}

        // Option 4: Light (Minimal & Clean)
        // mapStyle={`https://api.mapbox.com/styles/v1/mapbox/light-v11?access_token=${MAPBOX_TOKEN}`}

        // Option 5: Outdoors (Topographic)
        // mapStyle={`https://api.mapbox.com/styles/v1/mapbox/outdoors-v12?access_token=${MAPBOX_TOKEN}`}
        >
            <NavigationControl position="top-right" />

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
        </Map>
    );
}

// Helper function to extract coordinates from geometry
function getCoordinates(geometry: any): number[][] {
    const coords: number[][] = [];

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
