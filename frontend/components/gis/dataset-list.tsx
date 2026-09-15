"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useGISDatasets } from '@/lib/hooks/useGISDatasets';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
    Eye,
    Trash2,
    Upload,
    Search,
    FileJson,
    Database,
    Map as MapIcon,
    FileArchive,
    Loader2,
    AlertCircle
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import type { GISDataset } from '@/lib/types/gis';

const FILE_TYPE_COLORS = {
    geojson: 'bg-green-500/10 text-green-700 border-green-200',
    shapefile: 'bg-blue-500/10 text-blue-700 border-blue-200',
    kml: 'bg-purple-500/10 text-purple-700 border-purple-200',
    geopackage: 'bg-orange-500/10 text-orange-700 border-orange-200',
};

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

export function DatasetList() {
    const router = useRouter();
    const { datasets, isLoading, error, refetch, deleteDataset, isDeleting } = useGISDatasets();
    const [searchQuery, setSearchQuery] = useState('');
    const [datasetToDelete, setDatasetToDelete] = useState<string | null>(null);

    // Filter datasets by search query
    const filteredDatasets = datasets.filter((dataset) =>
        dataset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        dataset.description?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const handleView = (datasetId: string) => {
        router.push(`/dashboard/admin/gis-datasets/${datasetId}`);
    };

    const handleDelete = (datasetId: string) => {
        setDatasetToDelete(datasetId);
    };

    const confirmDelete = () => {
        if (datasetToDelete) {
            deleteDataset(datasetToDelete);
            setDatasetToDelete(null);
        }
    };

    const getFileTypeIcon = (fileType: string) => {
        const Icon = FILE_TYPE_ICONS[fileType as keyof typeof FILE_TYPE_ICONS] || FileArchive;
        return <Icon className="h-4 w-4" />;
    };

    const getTotalFeatures = (dataset: GISDataset) => {
        // Use total_features from dataset if available (new backend)
        if (dataset.total_features !== undefined) {
            return dataset.total_features;
        }
        // Fallback to calculating from layers (old backend)
        if (!dataset.layers || dataset.layers.length === 0) {
            return 0;
        }
        return dataset.layers.reduce((sum, layer) => sum + layer.feature_count, 0);
    };

    // Error state
    if (error) {
        return (
            <Card>
                <CardContent className="flex flex-col items-center justify-center py-16">
                    <AlertCircle className="h-16 w-16 text-destructive mb-4" />
                    <h3 className="text-lg font-semibold mb-2">Failed to Load Datasets</h3>
                    <p className="text-muted-foreground text-center mb-4 max-w-md">
                        {(error as any)?.response?.status === 401
                            ? 'Your session may have expired. Please login again.'
                            : 'Unable to fetch datasets. Please check your connection and try again.'}
                    </p>
                    <div className="flex gap-2">
                        <Button onClick={() => refetch()} variant="outline">
                            Try Again
                        </Button>
                        {(error as any)?.response?.status === 401 && (
                            <Button onClick={() => router.push('/login')}>
                                Login Again
                            </Button>
                        )}
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="text-center">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
                    <p className="text-sm text-muted-foreground">Loading datasets...</p>
                </div>
            </div>
        );
    }

    return (
        <>
            <div className="space-y-4">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-bold">GIS Datasets</h2>
                        <p className="text-muted-foreground">
                            Manage your geographic information system datasets
                        </p>
                    </div>
                    <Button onClick={() => router.push('/dashboard/admin/gis-datasets/upload')}>
                        <Upload className="mr-2 h-4 w-4" />
                        Upload Dataset
                    </Button>
                </div>

                {/* Search */}
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search datasets..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10"
                    />
                </div>

                {/* Datasets Table */}
                {filteredDatasets.length === 0 ? (
                    <Card>
                        <CardContent className="flex flex-col items-center justify-center py-16">
                            <Database className="h-16 w-16 text-muted-foreground mb-4" />
                            <h3 className="text-lg font-semibold mb-2">
                                {searchQuery ? 'No datasets found' : 'No datasets yet'}
                            </h3>
                            <p className="text-muted-foreground text-center mb-4">
                                {searchQuery
                                    ? 'Try adjusting your search query'
                                    : 'Upload your first GIS dataset to get started'}
                            </p>
                            {!searchQuery && (
                                <Button onClick={() => router.push('/dashboard/admin/gis-datasets/upload')}>
                                    <Upload className="mr-2 h-4 w-4" />
                                    Upload Dataset
                                </Button>
                            )}
                        </CardContent>
                    </Card>
                ) : (
                    <Card>
                        <CardContent className="p-0">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Name</TableHead>
                                        <TableHead>Type</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Features</TableHead>
                                        <TableHead>Layers</TableHead>
                                        <TableHead>Created</TableHead>
                                        <TableHead className="text-right">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {filteredDatasets.map((dataset) => (
                                        <TableRow key={dataset.id}>
                                            <TableCell>
                                                <div>
                                                    <p className="font-medium">{dataset.name}</p>
                                                    {dataset.description && (
                                                        <p className="text-sm text-muted-foreground line-clamp-1">
                                                            {dataset.description}
                                                        </p>
                                                    )}
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <Badge
                                                    variant="outline"
                                                    className={FILE_TYPE_COLORS[dataset.file_type]}
                                                >
                                                    <span className="mr-1">{getFileTypeIcon(dataset.file_type)}</span>
                                                    {dataset.file_type}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>
                                                <Badge
                                                    variant="outline"
                                                    className={STATUS_COLORS[dataset.status]}
                                                >
                                                    {dataset.status === 'processing' && (
                                                        <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                                                    )}
                                                    {dataset.status === 'failed' && (
                                                        <AlertCircle className="mr-1 h-3 w-3" />
                                                    )}
                                                    {dataset.status}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>{getTotalFeatures(dataset).toLocaleString()}</TableCell>
                                            <TableCell>{dataset.total_layers ?? dataset.layers?.length ?? 0}</TableCell>
                                            <TableCell className="text-muted-foreground">
                                                {formatDistanceToNow(new Date(dataset.created_at), { addSuffix: true })}
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <div className="flex items-center justify-end gap-2">
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => handleView(dataset.id)}
                                                        title="View dataset"
                                                    >
                                                        <Eye className="h-4 w-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        onClick={() => handleDelete(dataset.id)}
                                                        disabled={isDeleting}
                                                        title="Delete dataset"
                                                    >
                                                        <Trash2 className="h-4 w-4 text-destructive" />
                                                    </Button>
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </CardContent>
                    </Card>
                )}
            </div>

            {/* Delete Confirmation Dialog */}
            <AlertDialog open={!!datasetToDelete} onOpenChange={() => setDatasetToDelete(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                        <AlertDialogDescription>
                            This action cannot be undone. This will permanently delete the dataset
                            and all associated layers.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={confirmDelete}
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </>
    );
}
