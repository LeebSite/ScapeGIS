"use client";

import { useRouter } from 'next/navigation';
import { useGISDataset } from '@/lib/hooks/useGISDatasets';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import {
    ArrowLeft,
    Trash2,
    Loader2,
    AlertCircle,
    FileJson,
    Database,
    Map as MapIcon,
    FileArchive,
    Layers,
    MapPin,
    Calendar,
    FileText,
    Globe
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import type { GISDataset, GISLayer } from '@/lib/types/gis';

interface DatasetDetailProps {
    datasetId: string;
    children?: React.ReactNode;
}

const FILE_TYPE_ICONS = {
    geojson: FileJson,
    shapefile: Database,
    kml: MapIcon,
    geopackage: FileArchive,
};

const STATUS_COLORS = {
    completed: 'bg-green-500/10 text-green-700 border-green-200',
    processing: 'bg-yellow-500/10 text-yellow-700 border-yellow-200',
    failed: 'bg-red-500/10 text-red-700 border-red-200',
    pending: 'bg-gray-500/10 text-gray-700 border-gray-200',
};

export function DatasetDetail({ datasetId, children }: DatasetDetailProps) {
    const router = useRouter();
    const { dataset, isLoading, deleteDataset, isDeleting } = useGISDataset(datasetId);

    const handleDelete = () => {
        deleteDataset();
        // Navigate back after a short delay
        setTimeout(() => {
            router.push('/dashboard/admin/gis-datasets');
        }, 500);
    };

    const getFileTypeIcon = (fileType: string) => {
        const Icon = FILE_TYPE_ICONS[fileType as keyof typeof FILE_TYPE_ICONS] || FileArchive;
        return <Icon className="h-5 w-5" />;
    };

    const getTotalFeatures = () => {
        if (!dataset) return 0;
        return dataset.layers.reduce((sum, layer) => sum + layer.feature_count, 0);
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-center">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
                    <p className="text-sm text-muted-foreground">Loading dataset...</p>
                </div>
            </div>
        );
    }

    if (!dataset) {
        return (
            <Card>
                <CardContent className="flex flex-col items-center justify-center py-16">
                    <AlertCircle className="h-16 w-16 text-destructive mb-4" />
                    <h3 className="text-lg font-semibold mb-2">Dataset not found</h3>
                    <p className="text-muted-foreground mb-4">
                        The dataset you're looking for doesn't exist or you don't have access to it.
                    </p>
                    <Button onClick={() => router.push('/dashboard/admin/gis-datasets')}>
                        <ArrowLeft className="mr-2 h-4 w-4" />
                        Back to Datasets
                    </Button>
                </CardContent>
            </Card>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div className="space-y-1 flex-1">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => router.push('/dashboard/admin/gis-datasets')}
                        className="mb-2"
                    >
                        <ArrowLeft className="mr-2 h-4 w-4" />
                        Back to Datasets
                    </Button>
                    <h1 className="text-3xl font-bold">{dataset.name}</h1>
                    {dataset.description && (
                        <p className="text-muted-foreground">{dataset.description}</p>
                    )}
                </div>

                <AlertDialog>
                    <AlertDialogTrigger asChild>
                        <Button variant="destructive" disabled={isDeleting}>
                            {isDeleting ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                                <Trash2 className="mr-2 h-4 w-4" />
                            )}
                            Delete Dataset
                        </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                        <AlertDialogHeader>
                            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                            <AlertDialogDescription>
                                This action cannot be undone. This will permanently delete the dataset
                                "{dataset.name}" and all associated layers.
                            </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                                onClick={handleDelete}
                                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            >
                                Delete
                            </AlertDialogAction>
                        </AlertDialogFooter>
                    </AlertDialogContent>
                </AlertDialog>
            </div>

            {/* Metadata Card */}
            <Card>
                <CardHeader>
                    <CardTitle>Dataset Information</CardTitle>
                    <CardDescription>Metadata and statistics for this dataset</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {/* File Type */}
                        <div className="space-y-1">
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                {getFileTypeIcon(dataset.file_type)}
                                <span>File Type</span>
                            </div>
                            <p className="font-medium capitalize">{dataset.file_type}</p>
                        </div>

                        {/* Status */}
                        <div className="space-y-1">
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <AlertCircle className="h-4 w-4" />
                                <span>Status</span>
                            </div>
                            <Badge variant="outline" className={STATUS_COLORS[dataset.status]}>
                                {dataset.status}
                            </Badge>
                        </div>

                        {/* Total Features */}
                        <div className="space-y-1">
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <MapPin className="h-4 w-4" />
                                <span>Total Features</span>
                            </div>
                            <p className="font-medium">{getTotalFeatures().toLocaleString()}</p>
                        </div>

                        {/* Number of Layers */}
                        <div className="space-y-1">
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <Layers className="h-4 w-4" />
                                <span>Layers</span>
                            </div>
                            <p className="font-medium">{dataset.layers.length}</p>
                        </div>

                        {/* File Size */}
                        {dataset.file_size && (
                            <div className="space-y-1">
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <FileText className="h-4 w-4" />
                                    <span>File Size</span>
                                </div>
                                <p className="font-medium">
                                    {(dataset.file_size / 1024 / 1024).toFixed(2)} MB
                                </p>
                            </div>
                        )}

                        {/* CRS */}
                        {dataset.crs && (
                            <div className="space-y-1">
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <Globe className="h-4 w-4" />
                                    <span>CRS</span>
                                </div>
                                <p className="font-medium">{dataset.crs}</p>
                            </div>
                        )}

                        {/* Created */}
                        <div className="space-y-1">
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <Calendar className="h-4 w-4" />
                                <span>Created</span>
                            </div>
                            <p className="font-medium">
                                {formatDistanceToNow(new Date(dataset.created_at), { addSuffix: true })}
                            </p>
                        </div>

                        {/* Visibility */}
                        <div className="space-y-1">
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <Globe className="h-4 w-4" />
                                <span>Visibility</span>
                            </div>
                            <Badge variant={dataset.is_public ? "default" : "secondary"}>
                                {dataset.is_public ? 'Public' : 'Private'}
                            </Badge>
                        </div>
                    </div>

                    {/* Error Message */}
                    {dataset.status === 'failed' && dataset.error_message && (
                        <>
                            <Separator />
                            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
                                <div className="flex items-start gap-2">
                                    <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
                                    <div>
                                        <p className="font-medium text-destructive">Processing Error</p>
                                        <p className="text-sm text-muted-foreground mt-1">
                                            {dataset.error_message}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </>
                    )}

                    {/* Layers Info */}
                    {dataset.layers.length > 0 && (
                        <>
                            <Separator />
                            <div>
                                <h4 className="font-medium mb-3">Layers ({dataset.layers.length})</h4>
                                <div className="space-y-2">
                                    {dataset.layers.map((layer) => (
                                        <div
                                            key={layer.id}
                                            className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
                                        >
                                            <div className="flex-1">
                                                <p className="font-medium">{layer.name}</p>
                                                {layer.description && (
                                                    <p className="text-sm text-muted-foreground">{layer.description}</p>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-4 text-sm text-muted-foreground">
                                                <span>{layer.geometry_type}</span>
                                                <span>{layer.feature_count} features</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </>
                    )}
                </CardContent>
            </Card>

            {/* Map preview or custom children */}
            {children}
        </div>
    );
}
