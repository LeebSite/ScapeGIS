"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { GISService } from '@/lib/api/GISService';
import { Upload, Loader2, FileArchive, X, CheckCircle, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

const uploadSchema = z.object({
    name: z.string().min(1, 'Dataset name is required').max(100, 'Name must be less than 100 characters'),
    description: z.string().max(500, 'Description must be less than 500 characters').optional(),
    is_public: z.boolean().default(false),
});

type UploadFormData = z.infer<typeof uploadSchema>;

export function UploadForm() {
    const router = useRouter();
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [uploadError, setUploadError] = useState<string | null>(null);
    const [uploadSuccess, setUploadSuccess] = useState(false);

    const {
        register,
        handleSubmit,
        formState: { errors },
        reset
    } = useForm<UploadFormData>({
        resolver: zodResolver(uploadSchema),
        defaultValues: {
            is_public: false,
        }
    });

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploadError(null);
        setUploadSuccess(false);

        //Validate file type
        if (!file.name.endsWith('.zip')) {
            const error = 'Please select a ZIP file';
            setUploadError(error);
            toast.error(error, { duration: 5000 });
            e.target.value = '';
            return;
        }

        // Validate file size
        if (file.size > MAX_FILE_SIZE) {
            const error = 'File size must be less than 50MB';
            setUploadError(error);
            toast.error(error, { duration: 5000 });
            e.target.value = '';
            return;
        }

        setSelectedFile(file);
    };

    const onSubmit = async (data: UploadFormData) => {
        if (!selectedFile) {
            const error = 'Please select a file to upload';
            setUploadError(error);
            toast.error(error, { duration: 5000 });
            return;
        }

        setUploading(true);
        setProgress(0);
        setUploadError(null);
        setUploadSuccess(false);

        try {
            const dataset = await GISService.uploadGISFile(
                selectedFile,
                data.name,
                data.description,
                data.is_public,
                (percent) => setProgress(percent)
            );

            setUploadSuccess(true);
            toast.success('Dataset uploaded successfully!', {
                description: `"${dataset.name}" is now being processed. Redirecting...`,
                duration: 5000,
            });

            // Reset form
            reset();
            setSelectedFile(null);

            // Redirect to dataset detail page after short delay
            setTimeout(() => {
                router.push(`/dashboard/admin/gis-datasets/${dataset.id}`);
            }, 2000);

        } catch (error: any) {
            console.error('Upload error:', error);

            // Extract detailed error message
            const errorMessage = error.response?.data?.detail
                || error.response?.data?.message
                || error.message
                || 'Failed to upload file. Please try again.';

            const statusCode = error.response?.status;

            let displayError = errorMessage;
            if (statusCode === 404) {
                displayError = '❌ Upload endpoint not found. Backend may not be running or endpoint is incorrect.\n\n' +
                    'Expected endpoint: http://localhost:8000/api/v1/gis/upload\n' +
                    'Please check:\n' +
                    '1. Backend server is running (uvicorn app.main:app)\n' +
                    '2. Backend is accessible at http://localhost:8000\n' +
                    '3. GIS router is properly registered';
            } else if (statusCode === 401 || statusCode === 403) {
                displayError = '🔒 Unauthorized. Your session may have expired. Please login again.';
            } else if (statusCode >= 500) {
                displayError = '⚠️ Server error occurred while processing your upload.\n\nError: ' + errorMessage + '\n\nPlease check backend logs for more details.';
            }

            setUploadError(displayError);

            toast.error('Upload Failed', {
                description: displayError,
                duration: 15000, // 15 seconds for error - longer than before
            });
        } finally {
            setUploading(false);
            setProgress(0);
        }
    };

    const removeFile = () => {
        setSelectedFile(null);
        setUploadError(null);
        setUploadSuccess(false);
        const fileInput = document.getElementById('file-input') as HTMLInputElement;
        if (fileInput) fileInput.value = '';
    };

    return (
        <Card className="max-w-2xl mx-auto">
            <CardHeader>
                <CardTitle>Upload GIS Dataset</CardTitle>
                <CardDescription>
                    Upload a ZIP file containing GIS data (GeoJSON, Shapefile, KML, or GeoPackage)
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">

                    {/* Error Alert */}
                    {uploadError && (
                        <Alert variant="destructive" className="animate-in fade-in slide-in-from-top-2 relative">
                            <AlertCircle className="h-4 w-4" />
                            <AlertDescription className="ml-2 pr-8">
                                <p className="font-semibold">Upload Error</p>
                                <p className="text-sm mt-1 whitespace-pre-line">{uploadError}</p>
                            </AlertDescription>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="absolute top-2 right-2 h-6 w-6"
                                onClick={() => setUploadError(null)}
                            >
                                <X className="h-4 w-4" />
                            </Button>
                        </Alert>
                    )}

                    {/* Success Alert */}
                    {uploadSuccess && (
                        <Alert className="border-green-500 bg-green-50 text-green-900 animate-in fade-in slide-in-from-top-2">
                            <CheckCircle className="h-4 w-4 text-green-600" />
                            <AlertDescription className="ml-2">
                                <p className="font-semibold text-green-900">Upload Successful!</p>
                                <p className="text-sm mt-1 text-green-800">Your dataset is being processed. Redirecting to detail page...</p>
                            </AlertDescription>
                        </Alert>
                    )}

                    {/* File Upload */}
                    <div className="space-y-2">
                        <Label htmlFor="file-input">ZIP File *</Label>
                        {!selectedFile ? (
                            <div className="border-2 border-dashed rounded-lg p-8 text-center hover:border-primary transition-all hover:bg-muted/50">
                                <input
                                    id="file-input"
                                    type="file"
                                    accept=".zip"
                                    onChange={handleFileChange}
                                    disabled={uploading}
                                    className="hidden"
                                />
                                <label
                                    htmlFor="file-input"
                                    className="cursor-pointer flex flex-col items-center"
                                >
                                    <FileArchive className="h-12 w-12 text-muted-foreground mb-4 animate-pulse" />
                                    <p className="text-sm font-medium mb-1">
                                        Click to upload or drag and drop
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                        ZIP files only (max 50MB)
                                    </p>
                                </label>
                            </div>
                        ) : (
                            <div className="border rounded-lg p-4 flex items-center justify-between bg-muted/50 animate-in fade-in slide-in-from-bottom-2">
                                <div className="flex items-center gap-3">
                                    <FileArchive className="h-8 w-8 text-primary" />
                                    <div>
                                        <p className="text-sm font-medium">{selectedFile.name}</p>
                                        <p className="text-xs text-muted-foreground">
                                            {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                                        </p>
                                    </div>
                                </div>
                                <Button
                                    type="button"
                                    variant="ghost"
                                    size="icon"
                                    onClick={removeFile}
                                    disabled={uploading}
                                >
                                    <X className="h-4 w-4" />
                                </Button>
                            </div>
                        )}
                    </div>

                    {/* Dataset Name */}
                    <div className="space-y-2">
                        <Label htmlFor="name">Dataset Name *</Label>
                        <Input
                            id="name"
                            {...register('name')}
                            placeholder="e.g., Kantor Gubernur Riau"
                            disabled={uploading}
                        />
                        {errors.name && (
                            <p className="text-sm text-destructive animate-in fade-in">{errors.name.message}</p>
                        )}
                    </div>

                    {/* Description */}
                    <div className="space-y-2">
                        <Label htmlFor="description">Description (Optional)</Label>
                        <Textarea
                            id="description"
                            {...register('description')}
                            placeholder="Describe your dataset..."
                            rows={3}
                            disabled={uploading}
                        />
                        {errors.description && (
                            <p className="text-sm text-destructive animate-in fade-in">{errors.description.message}</p>
                        )}
                    </div>

                    {/* Public Checkbox */}
                    <div className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            id="is_public"
                            {...register('is_public')}
                            disabled={uploading}
                            className="rounded border-gray-300"
                        />
                        <Label htmlFor="is_public" className="font-normal cursor-pointer">
                            Make this dataset public
                        </Label>
                    </div>

                    {/* Upload Progress */}
                    {uploading && (
                        <div className="space-y-4 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg border-2 border-blue-200 dark:border-blue-800 animate-in fade-in slide-in-from-bottom-2">
                            <div className="flex items-center gap-3 mb-2">
                                <div className="relative">
                                    <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                                    <div className="absolute inset-0 h-6 w-6 rounded-full bg-blue-200 animate-ping opacity-75" />
                                </div>
                                <div>
                                    <p className="text-sm font-semibold text-blue-900 dark:text-blue-100">
                                        Uploading Your Dataset
                                    </p>
                                    <p className="text-xs text-blue-700 dark:text-blue-300">
                                        {progress < 30 ? 'Preparing upload...' :
                                            progress < 70 ? 'Transferring data...' :
                                                progress < 95 ? 'Processing file...' :
                                                    'Almost done...'}
                                    </p>
                                </div>
                            </div>

                            {/* Progress Bar */}
                            <div className="relative h-4 bg-blue-100 dark:bg-blue-900 rounded-full overflow-hidden shadow-inner">
                                <div
                                    className="absolute inset-0 bg-gradient-to-r from-blue-500 via-blue-600 to-primary transition-all duration-500 ease-out rounded-full shadow-lg"
                                    style={{ width: `${progress}%` }}
                                >
                                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
                                </div>
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <span className="text-xs font-bold text-blue-900 dark:text-blue-100 drop-shadow-sm">
                                        {progress}%
                                    </span>
                                </div>
                            </div>

                            <p className="text-xs text-center text-blue-700 dark:text-blue-300">
                                Please wait while your file is being uploaded and processed...
                            </p>
                        </div>
                    )}

                    {/* Submit Button */}
                    <Button
                        type="submit"
                        disabled={uploading || !selectedFile || uploadSuccess}
                        className="w-full transition-all hover:scale-[1.02]"
                        size="lg"
                    >
                        {uploading ? (
                            <>
                                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                Uploading... {progress}%
                            </>
                        ) : uploadSuccess ? (
                            <>
                                <CheckCircle className="mr-2 h-5 w-5" />
                                Upload Complete!
                            </>
                        ) : (
                            <>
                                <Upload className="mr-2 h-5 w-5" />
                                Upload Dataset
                            </>
                        )}
                    </Button>
                </form>
            </CardContent>
        </Card>
    );
}
