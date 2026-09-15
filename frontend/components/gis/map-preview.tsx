"use client";

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { GISService } from '@/lib/api/GISService';
import type { GeoJSONFeatureCollection } from '@/lib/types/gis';
import { Loader2, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';

// Dynamically import Mapbox map component
const MapboxMap = dynamic(() => import('./mapbox-map'), {
    ssr: false,
    loading: () => (
        <div className="flex items-center justify-center h-[600px] bg-muted rounded-lg">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
    ),
});

interface MapPreviewProps {
    layerId: string;
    className?: string;
}

export function MapPreview({ layerId, className = '' }: MapPreviewProps) {
    const [geojson, setGeojson] = useState<GeoJSONFeatureCollection | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadGeoJSON();
    }, [layerId]);

    const loadGeoJSON = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await GISService.getLayerGeoJSON(layerId);
            console.log('Loaded GeoJSON:', data);
            setGeojson(data);
        } catch (err: any) {
            console.error('Failed to load GeoJSON:', err);
            setError(err.response?.data?.detail || err.message || 'Failed to load map data');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className={`rounded-lg overflow-hidden border ${className}`}>
                <div className="flex items-center justify-center h-[600px] bg-muted">
                    <div className="text-center">
                        <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
                        <p className="text-sm text-muted-foreground">Loading map data...</p>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className={`rounded-lg overflow-hidden border ${className}`}>
                <div className="flex flex-col items-center justify-center h-[600px] bg-muted p-8">
                    <Alert variant="destructive" className="max-w-md">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                            <p className="font-semibold mb-2">Failed to load map</p>
                            <p className="text-sm">{error}</p>
                        </AlertDescription>
                    </Alert>
                    <Button onClick={loadGeoJSON} variant="outline" className="mt-4">
                        Retry
                    </Button>
                </div>
            </div>
        );
    }

    if (!geojson || geojson.features.length === 0) {
        return (
            <div className={`rounded-lg overflow-hidden border ${className}`}>
                <div className="flex items-center justify-center h-[600px] bg-muted">
                    <p className="text-muted-foreground">No features to display</p>
                </div>
            </div>
        );
    }

    return (
        <div className={`rounded-lg overflow-hidden border ${className}`}>
            <MapboxMap geojson={geojson} />
        </div>
    );
}

export default MapPreview;
