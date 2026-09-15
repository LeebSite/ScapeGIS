import { useEffect, useState } from "react";
import { layerAPI, subscriptionAPI } from "@/lib/api";
import type { Layer, Subscription } from "@/lib/types";
import { Check, Plus, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useAuthStore } from "@/lib/store";

interface LayerSelectorProps {
    onSelect: (layer: Layer) => void;
    selectedLayerIds: string[];
}

export function LayerSelector({ onSelect, selectedLayerIds }: LayerSelectorProps) {
    const [layers, setLayers] = useState<Layer[]>([]);
    const [subscription, setSubscription] = useState<Subscription | null>(null);
    const [searchTerm, setSearchTerm] = useState("");
    const { user } = useAuthStore();
    const [isLoading, setIsLoading] = useState(true);

    // Hierarchy based on prompt
    const hierarchy: Record<string, number> = {
        free: 0,
        basic: 1,
        professional: 2
    };

    const hasAccess = (layer: Layer) => {
        if (!subscription) return false;

        // Subscription name from backend is Title Case (Free, Basic, Professional)
        // Layer level is lowercase (free, basic, professional)
        const userLevel = subscription.name.toLowerCase();
        const layerLevel = layer.subscription_level.toLowerCase();

        const userScore = hierarchy[userLevel] ?? 0;
        const layerScore = hierarchy[layerLevel] ?? 0;

        return layerScore <= userScore;
    };

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [layersRes, subRes] = await Promise.all([
                    layerAPI.getAvailableLayers(),
                    subscriptionAPI.getCurrentSubscription()
                ]);
                setLayers(layersRes.data);
                setSubscription(subRes.data);
            } catch (error) {
                console.error("Failed to fetch data:", error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, []);

    const filteredLayers = layers.filter(layer =>
        layer.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="space-y-4">
            <Input
                placeholder="Search layers..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
            />
            <ScrollArea className="h-[400px] border rounded-md p-4">
                {isLoading ? (
                    <div className="text-center text-sm text-muted-foreground">Loading layers...</div>
                ) : filteredLayers.length === 0 ? (
                    <div className="text-center text-sm text-muted-foreground">No layers found.</div>
                ) : (
                    <div className="grid gap-4">
                        {filteredLayers.map((layer) => {
                            const isSelected = selectedLayerIds.includes(layer.id);
                            const locked = !hasAccess(layer);

                            return (
                                <Card key={layer.id} className={`flex items-center justify-between p-3 ${isSelected ? 'border-primary' : ''} ${locked ? 'opacity-70' : ''}`}>
                                    <div className="flex flex-col gap-1">
                                        <div className="flex items-center gap-2">
                                            <span className="font-medium">{layer.name}</span>
                                            <Badge variant="outline" className="text-xs">{layer.type}</Badge>
                                            {layer.subscription_level !== 'free' && (
                                                <Badge variant="secondary" className="text-xs">{layer.subscription_level}</Badge>
                                            )}
                                        </div>
                                        <span className="text-xs text-muted-foreground">{layer.region}</span>
                                    </div>
                                    <Button
                                        size="sm"
                                        variant={isSelected ? "secondary" : "outline"}
                                        disabled={locked}
                                        onClick={() => !isSelected && onSelect(layer)}
                                    >
                                        {isSelected ? <Check className="h-4 w-4" /> : locked ? <Lock className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
                                    </Button>
                                </Card>
                            );
                        })}
                    </div>
                )}
            </ScrollArea>
        </div>
    );
}
