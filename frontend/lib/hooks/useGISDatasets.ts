/**
 * useGISDatasets - Hook for managing GIS datasets
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { GISService } from '@/lib/api/GISService';
import { toast } from 'sonner';
import type { GISDataset } from '@/lib/types/gis';

export const useGISDatasets = () => {
    const queryClient = useQueryClient();

    // Fetch all datasets
    const {
        data: datasets,
        isLoading,
        error,
        refetch,
    } = useQuery({
        queryKey: ['gis-datasets'],
        queryFn: () => GISService.getDatasets(),
        retry: 1, // Retry once on failure
        staleTime: 30000, // Cache for 30 seconds
    });

    // Delete dataset
    const deleteMutation = useMutation({
        mutationFn: (datasetId: string) => GISService.deleteDataset(datasetId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['gis-datasets'] });
            toast.success('Dataset deleted successfully');
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to delete dataset');
        },
    });

    return {
        datasets: datasets || [],
        isLoading,
        error,
        refetch,
        deleteDataset: deleteMutation.mutate,
        isDeleting: deleteMutation.isPending,
    };
};

export const useGISDataset = (datasetId: string) => {
    const queryClient = useQueryClient();

    // Fetch single dataset
    const {
        data: dataset,
        isLoading,
        error,
        refetch,
    } = useQuery({
        queryKey: ['gis-dataset', datasetId],
        queryFn: () => GISService.getDataset(datasetId),
        enabled: !!datasetId,
    });

    // Delete dataset
    const deleteMutation = useMutation({
        mutationFn: () => GISService.deleteDataset(datasetId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['gis-datasets'] });
            queryClient.invalidateQueries({ queryKey: ['gis-dataset', datasetId] });
            toast.success('Dataset deleted successfully');
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to delete dataset');
        },
    });

    return {
        dataset,
        isLoading,
        error,
        refetch,
        deleteDataset: deleteMutation.mutate,
        isDeleting: deleteMutation.isPending,
    };
};
