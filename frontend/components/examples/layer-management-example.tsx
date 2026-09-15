'use client';

import { useState } from 'react';
import { useLayers, useSearchLayers, useLayersByType } from '@/lib/hooks/useLayers';
import { useProjects, useProjectLayers, useAssignLayer } from '@/lib/hooks/useProjects';
import { usePermission } from '@/lib/hooks/usePermission';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Search, Map, Layers as LayersIcon } from 'lucide-react';

/**
 * Example component showing how to use all the new hooks
 * This demonstrates real-world usage patterns
 */
export function LayerManagementExample() {
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);

    // Fetch all layers
    const { layers: allLayers, isLoading: isLoadingLayers } = useLayers();

    // Fetch projects
    const { projects, isLoading: isLoadingProjects } = useProjects();

    // Search functionality
    const { layers: searchResults, isSearching } = useSearchLayers(searchQuery);

    // Get vector layers only
    const { layers: vectorLayers } = useLayersByType('vector');

    // Permission check
    const { hasPermission: canAssignLayers } = usePermission('projects.update');

    // Project layers (when project is selected)
    const { layers: projectLayers } = useProjectLayers(selectedProjectId || undefined);

    // Assign layer mutation
    const { assignLayer, isAssigning } = useAssignLayer();

    const handleAssignLayer = async (layerId: string) => {
        if (!selectedProjectId) return;

        try {
            await assignLayer({ projectId: selectedProjectId, layerId });
        } catch (error) {
            // Error automatically shown via toast
        }
    };

    // Decide which layers to display
    const displayLayers = searchQuery ? searchResults : allLayers;

    return (
        <div className="container mx-auto p-6 space-y-6">
            <div>
                <h1 className="text-3xl font-bold mb-2">Layer Management Demo</h1>
                <p className="text-muted-foreground">
                    Demonstrating useLayers, useProjects, and usePermission hooks
                </p>
            </div>

            {/* Search */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Search className="h-5 w-5" />
                        Search Layers
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="relative">
                        <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search layers by name or description..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-10"
                        />
                    </div>
                    {isSearching && (
                        <p className="text-sm text-muted-foreground mt-2">Searching...</p>
                    )}
                </CardContent>
            </Card>

            <Tabs defaultValue="all" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="all">All Layers ({allLayers.length})</TabsTrigger>
                    <TabsTrigger value="vector">Vector Only ({vectorLayers.length})</TabsTrigger>
                    <TabsTrigger value="projects">My Projects</TabsTrigger>
                </TabsList>

                {/* All Layers Tab */}
                <TabsContent value="all" className="space-y-4">
                    {isLoadingLayers ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {[1, 2, 3, 4, 5, 6].map((i) => (
                                <Skeleton key={i} className="h-32" />
                            ))}
                        </div>
                    ) : displayLayers.length === 0 ? (
                        <Card>
                            <CardContent className="py-12 text-center text-muted-foreground">
                                {searchQuery ? 'No layers found matching your search' : 'No layers available'}
                            </CardContent>
                        </Card>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {displayLayers.map((layer) => (
                                <Card key={layer.id} className="hover:shadow-lg transition-shadow">
                                    <CardHeader>
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-center gap-2">
                                                <LayersIcon className="h-5 w-5 text-primary" />
                                                <CardTitle className="text-lg">{layer.name}</CardTitle>
                                            </div>
                                            <Badge variant={layer.type === 'vector' ? 'default' : 'secondary'}>
                                                {layer.type}
                                            </Badge>
                                        </div>
                                        <CardDescription>{layer.region}</CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm text-muted-foreground">Subscription</span>
                                            <Badge variant="outline" className="capitalize">
                                                {layer.subscription_level}
                                            </Badge>
                                        </div>

                                        {canAssignLayers && selectedProjectId && (
                                            <Button
                                                size="sm"
                                                className="w-full"
                                                onClick={() => handleAssignLayer(layer.id)}
                                                disabled={isAssigning}
                                            >
                                                {isAssigning ? 'Assigning...' : 'Assign to Project'}
                                            </Button>
                                        )}
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}
                </TabsContent>

                {/* Vector Layers Tab */}
                <TabsContent value="vector" className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {vectorLayers.map((layer) => (
                            <Card key={layer.id}>
                                <CardHeader>
                                    <CardTitle className="text-lg flex items-center gap-2">
                                        <Map className="h-4 w-4" />
                                        {layer.name}
                                    </CardTitle>
                                    <CardDescription>{layer.region}</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <Badge>{layer.subscription_level}</Badge>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </TabsContent>

                {/* Projects Tab */}
                <TabsContent value="projects" className="space-y-4">
                    {isLoadingProjects ? (
                        <div className="space-y-2">
                            {[1, 2, 3].map((i) => (
                                <Skeleton key={i} className="h-20" />
                            ))}
                        </div>
                    ) : projects.length === 0 ? (
                        <Card>
                            <CardContent className="py-12 text-center text-muted-foreground">
                                No projects yet. Create your first project!
                            </CardContent>
                        </Card>
                    ) : (
                        <div className="grid grid-cols-1 gap-4">
                            {projects.map((project) => (
                                <Card
                                    key={project.id}
                                    className={`cursor-pointer transition-all ${selectedProjectId === project.id ? 'ring-2 ring-primary' : ''
                                        }`}
                                    onClick={() => setSelectedProjectId(project.id)}
                                >
                                    <CardHeader>
                                        <CardTitle>{project.name}</CardTitle>
                                        <CardDescription>{project.description}</CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        {selectedProjectId === project.id && (
                                            <div className="mt-4 space-y-2">
                                                <h4 className="font-semibold text-sm">Assigned Layers:</h4>
                                                {projectLayers.length === 0 ? (
                                                    <p className="text-sm text-muted-foreground">
                                                        No layers assigned yet
                                                    </p>
                                                ) : (
                                                    <div className="flex flex-wrap gap-2">
                                                        {projectLayers.map((layer) => (
                                                            <Badge key={layer.id} variant="secondary">
                                                                {layer.name}
                                                            </Badge>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}
                </TabsContent>
            </Tabs>

            {/* Stats Card */}
            <Card>
                <CardHeader>
                    <CardTitle>Quick Stats</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                            <p className="text-sm text-muted-foreground">Total Layers</p>
                            <p className="text-2xl font-bold">{allLayers.length}</p>
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground">Vector Layers</p>
                            <p className="text-2xl font-bold">{vectorLayers.length}</p>
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground">My Projects</p>
                            <p className="text-2xl font-bold">{projects.length}</p>
                        </div>
                        <div>
                            <p className="text-sm text-muted-foreground">Can Assign Layers</p>
                            <p className="text-2xl font-bold">{canAssignLayers ? 'Yes' : 'No'}</p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
