"use client";

import { useParams } from 'next/navigation';
import dynamic from 'next/dynamic';
import { DatasetDetail } from '@/components/gis/dataset-detail';
import { useGISDataset } from '@/lib/hooks/useGISDatasets';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2 } from 'lucide-react';

// Dynamic import to avoid SSR issues with Leaflet
const MapPreview = dynamic(
    () => import('@/components/gis/map-preview'),
    {
        ssr: false,
        loading: () => (
            <div className="flex items-center justify-center h-[600px] bg-muted rounded-lg">
                <div className="text-center">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
                    <p className="text-sm text-muted-foreground">Loading map...</p>
                </div>
            </div>
        ),
    }
);

export default function DatasetDetailPage() {
    const params = useParams();
    const datasetId = params.id as string;
    const { dataset } = useGISDataset(datasetId);

    return (
        <div className="container mx-auto py-8">
            <DatasetDetail datasetId={datasetId}>
                {/* Show map only if dataset is completed and has layers */}
                {dataset?.status === 'completed' && dataset.layers && dataset.layers.length > 0 && (
                    <Card>
                        <CardHeader>
                            <CardTitle>Map Preview</CardTitle>
                        </CardHeader>
                        <CardContent>
                            {dataset.layers.length === 1 ? (
                                // Single layer - show directly
                                <MapPreview layerId={dataset.layers[0].id} />
                            ) : (
                                // Multiple layers - show in tabs
                                <Tabs defaultValue={dataset.layers[0].id} className="w-full">
                                    <TabsList className="mb-4">
                                        {dataset.layers.map((layer) => (
                                            <TabsTrigger key={layer.id} value={layer.id}>
                                                {layer.name} ({layer.feature_count} features)
                                            </TabsTrigger>
                                        ))}
                                    </TabsList>
                                    {dataset.layers.map((layer) => (
                                        <TabsContent key={layer.id} value={layer.id}>
                                            <MapPreview layerId={layer.id} />
                                        </TabsContent>
                                    ))}
                                </Tabs>
                            )}
                        </CardContent>
                    </Card>
                )}

                {/* Show processing message */}
                {dataset?.status === 'processing' && (
                    <Card>
                        <CardContent className="flex flex-col items-center justify-center py-16">
                            <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
                            <h3 className="text-lg font-semibold mb-2">Processing Dataset</h3>
                            <p className="text-muted-foreground text-center">
                                Your dataset is being processed. This may take a few moments.
                                <br />
                                Please refresh the page to see the latest status.
                            </p>
                        </CardContent>
                    </Card>
                )}

                {/* Show error if failed */}
                {dataset?.status === 'failed' && (
                    <Card>
                        <CardContent className="flex flex-col items-center justify-center py-16">
                            <p className="text-muted-foreground">
                                Map preview is not available because the dataset processing failed.
                            </p>
                        </CardContent>
                    </Card>
                )}
            </DatasetDetail>
        </div>
    );
}
