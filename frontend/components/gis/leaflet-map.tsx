"use client";

import { useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { GeoJSONFeatureCollection } from '@/lib/types/gis';

// Fix for default marker icons in Leaflet
if (typeof window !== 'undefined') {
    delete (L.Icon.Default.prototype as any)._getIconUrl;
    L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
        iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
    });
}

interface LeafletMapProps {
    geojson: GeoJSONFeatureCollection | null;
}

// Component to handle map bounds using useMap hook
function MapController({ geojson }: { geojson: GeoJSONFeatureCollection | null }) {
    const map = useMap();

    useEffect(() => {
        if (geojson && geojson.features.length > 0) {
            try {
                const geoJsonLayer = L.geoJSON(geojson as any);
                const bounds = geoJsonLayer.getBounds();
                if (bounds.isValid()) {
                    map.fitBounds(bounds, { padding: [50, 50] });
                }
            } catch (err) {
                console.error('Failed to fit bounds:', err);
            }
        }
    }, [geojson, map]);

    return null;
}

function LeafletMap({ geojson }: LeafletMapProps) {
    if (!geojson) return null;

    const getFeatureStyle = (feature: any) => {
        const geometryType = feature?.geometry?.type;

        if (geometryType === 'Point' || geometryType === 'MultiPoint') {
            return {
                color: '#ef4444',
                fillColor: '#ef4444',
                fillOpacity: 0.6,
                weight: 2,
                radius: 8,
            };
        } else if (geometryType === 'LineString' || geometryType === 'MultiLineString') {
            return {
                color: '#3b82f6',
                weight: 3,
                opacity: 0.7,
            };
        } else {
            return {
                color: '#3b82f6',
                fillColor: '#3b82f6',
                fillOpacity: 0.3,
                weight: 2,
            };
        }
    };

    const onEachFeature = (feature: any, layer: any) => {
        if (feature.properties) {
            const popupContent = Object.entries(feature.properties)
                .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
                .join('<br/>');

            layer.bindPopup(popupContent);

            layer.on({
                mouseover: (e: any) => {
                    const layer = e.target;
                    layer.setStyle({
                        weight: 5,
                        fillOpacity: 0.7,
                    });
                },
                mouseout: (e: any) => {
                    const layer = e.target;
                    layer.setStyle(getFeatureStyle(feature));
                },
            });
        }
    };

    const pointToLayer = (feature: any, latlng: any) => {
        return L.circleMarker(latlng, getFeatureStyle(feature) as any);
    };

    return (
        <MapContainer
            center={[0, 0]}
            zoom={2}
            style={{ height: '600px', width: '100%' }}
            className="z-0"
        >
            <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            <GeoJSON
                key={JSON.stringify(geojson)}
                data={geojson as any}
                style={getFeatureStyle}
                onEachFeature={onEachFeature}
                pointToLayer={pointToLayer}
            />

            <MapController geojson={geojson} />
        </MapContainer>
    );
}

export default LeafletMap;
