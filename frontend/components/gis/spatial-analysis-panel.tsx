"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
    MapPin, Compass, Navigation, Building2, Hospital, Church, Shield,
    Search, Sparkles, Loader2, Crosshair, Layers, RefreshCw, CheckCircle2,
    AlertCircle, FileText, ChevronRight
} from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
    SpatialService,
    type LayerSemanticResponse,
    type NearestFeatureResult,
    type RadiusSearchResult,
    type SpatialContextResponse,
    type ContainmentResult,
} from "@/lib/api/SpatialService";

interface SpatialAnalysisPanelProps {
    workspaceId: string;
    projectId?: string;
    selectedLocation: { latitude: number; longitude: number } | null;
    onLocationSelect: (loc: { latitude: number; longitude: number }) => void;
    onHighlightFeatures?: (fc: any) => void;
    className?: string;
}

const PEKANBARU_PRESETS = [
    { name: "Pusat Kota (Kantor Walikota)", lat: 0.5071, lng: 101.4478 },
    { name: "RSUD Arifin Achmad", lat: 0.5242, lng: 101.4485 },
    { name: "Kecamatan Tampan / Binawidya", lat: 0.4682, lng: 101.3789 },
    { name: "Bandara SSK II", lat: 0.4616, lng: 101.4444 },
    { name: "Kecamatan Rumbai", lat: 0.5620, lng: 101.4310 },
];

const DEFAULT_SUBCATEGORIES = [
    { value: "arterial_road", label: "Jalan Arteri (Main Highway)", category: "transportation" },
    { value: "collector_road", label: "Jalan Kolektor", category: "transportation" },
    { value: "local_road", label: "Jalan Lokal", category: "transportation" },
    { value: "hospital", label: "Rumah Sakit (Hospital)", category: "facilities" },
    { value: "clinic", label: "Klinik / Puskesmas", category: "facilities" },
    { value: "police_station", label: "Kantor Polisi (Police)", category: "facilities" },
    { value: "subdistrict_office", label: "Kantor Camat", category: "facilities" },
    { value: "mayor_office", label: "Kantor Walikota", category: "facilities" },
    { value: "village_office", label: "Kantor Lurah / Kades", category: "facilities" },
    { value: "mosque", label: "Masjid", category: "religious" },
    { value: "church", label: "Gereja", category: "religious" },
];

export function SpatialAnalysisPanel({
    workspaceId,
    projectId,
    selectedLocation,
    onLocationSelect,
    onHighlightFeatures,
    className = "",
}: SpatialAnalysisPanelProps) {
    // Coordinate states (default to Pekanbaru center if not selected)
    const [lat, setLat] = useState<string>(selectedLocation ? String(selectedLocation.latitude) : "0.507100");
    const [lng, setLng] = useState<string>(selectedLocation ? String(selectedLocation.longitude) : "101.447800");

    // Semantic catalog loaded from backend
    const [semanticLayers, setSemanticLayers] = useState<LayerSemanticResponse[]>([]);
    const [loadingSemantics, setLoadingSemantics] = useState(false);

    // Context analysis state
    const [contextLoading, setContextLoading] = useState(false);
    const [contextResult, setContextResult] = useState<SpatialContextResponse | null>(null);

    // Nearest feature state
    const [nearestSubcat, setNearestSubcat] = useState("arterial_road");
    const [nearestLoading, setNearestLoading] = useState(false);
    const [nearestResult, setNearestResult] = useState<NearestFeatureResult | null>(null);

    // Radius search state
    const [radiusSubcat, setRadiusSubcat] = useState("hospital");
    const [radiusMeters, setRadiusMeters] = useState(2000);
    const [radiusLoading, setRadiusLoading] = useState(false);
    const [radiusResult, setRadiusResult] = useState<RadiusSearchResult | null>(null);

    // Containment state
    const [containmentLoading, setContainmentLoading] = useState(false);
    const [containmentResult, setContainmentResult] = useState<ContainmentResult | null>(null);

    // Sync input when parent selectedLocation changes
    useEffect(() => {
        if (selectedLocation) {
            setLat(selectedLocation.latitude.toFixed(6));
            setLng(selectedLocation.longitude.toFixed(6));
        }
    }, [selectedLocation]);

    // Load available semantic layers for this workspace
    const fetchSemanticLayers = useCallback(async () => {
        if (!workspaceId) return;
        setLoadingSemantics(true);
        try {
            const data = await SpatialService.getSemanticLayers(workspaceId);
            setSemanticLayers(data);
        } catch {
            // Non-critical, fallback to presets
        } finally {
            setLoadingSemantics(false);
        }
    }, [workspaceId]);

    useEffect(() => {
        fetchSemanticLayers();
    }, [fetchSemanticLayers]);

    const getParsedCoords = (): { latitude: number; longitude: number } | null => {
        const latitude = parseFloat(lat);
        const longitude = parseFloat(lng);
        if (isNaN(latitude) || isNaN(longitude)) {
            toast.error("Format koordinat tidak valid.");
            return null;
        }
        if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
            toast.error("Koordinat berada di luar jangkauan WGS 84 valid.");
            return null;
        }
        return { latitude, longitude };
    };

    const handleApplyCoords = () => {
        const coords = getParsedCoords();
        if (coords) {
            onLocationSelect(coords);
            toast.info(`Lokasi disetel ke [${coords.latitude.toFixed(4)}, ${coords.longitude.toFixed(4)}]`);
        }
    };

    const handleSelectPreset = (preset: typeof PEKANBARU_PRESETS[0]) => {
        setLat(preset.lat.toFixed(6));
        setLng(preset.lng.toFixed(6));
        onLocationSelect({ latitude: preset.lat, longitude: preset.lng });
        toast.info(`Preset dipilih: ${preset.name}`);
    };

    // 1. Run Comprehensive Spatial Context
    const handleRunSpatialContext = async () => {
        const coords = getParsedCoords();
        if (!coords || !workspaceId) return;

        setContextLoading(true);
        setContextResult(null);
        try {
            const res = await SpatialService.getSpatialContext({
                latitude: coords.latitude,
                longitude: coords.longitude,
                workspace_id: workspaceId,
                project_id: projectId,
            });
            setContextResult(res);
            toast.success("Spatial Context berhasil dihitung via PostGIS!");
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Gagal mengambil spatial context.");
        } finally {
            setContextLoading(false);
        }
    };

    // 2. Run Nearest Feature Query
    const handleRunNearest = async () => {
        const coords = getParsedCoords();
        if (!coords || !workspaceId) return;

        setNearestLoading(true);
        setNearestResult(null);
        try {
            const res = await SpatialService.findNearest({
                latitude: coords.latitude,
                longitude: coords.longitude,
                subcategory: nearestSubcat,
                workspace_id: workspaceId,
            });
            setNearestResult(res);
            toast.success(`Objek terdekat ditemukan: ${res.distance_meters.toFixed(0)} m`);
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Objek terdekat tidak ditemukan untuk layer ini.");
        } finally {
            setNearestLoading(false);
        }
    };

    // 3. Run Radius Search Query
    const handleRunRadius = async () => {
        const coords = getParsedCoords();
        if (!coords || !workspaceId) return;

        setRadiusLoading(true);
        setRadiusResult(null);
        try {
            const res = await SpatialService.radiusSearch({
                latitude: coords.latitude,
                longitude: coords.longitude,
                subcategory: radiusSubcat,
                radius_meters: radiusMeters,
                workspace_id: workspaceId,
            });
            setRadiusResult(res);
            toast.success(`Ditemukan ${res.count} objek dalam radius ${radiusMeters} m`);
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Pencarian radius gagal.");
        } finally {
            setRadiusLoading(false);
        }
    };

    // 4. Run Containment Check (Administrative boundary)
    const handleRunContainment = async () => {
        const coords = getParsedCoords();
        if (!coords || !workspaceId) return;

        // Find administrative boundary layer from semanticLayers or fallback
        const adminLayer = semanticLayers.find(
            (l) => l.subcategory === "administrative_boundary" || l.category === "administrative"
        );
        if (!adminLayer) {
            toast.error("Layer batas administrasi belum terdaftar pada katalog semantik workspace ini.");
            return;
        }

        setContainmentLoading(true);
        setContainmentResult(null);
        try {
            const res = await SpatialService.checkContainment({
                latitude: coords.latitude,
                longitude: coords.longitude,
                layer_id: adminLayer.layer_id,
                workspace_id: workspaceId,
            });
            setContainmentResult(res);
            if (res) {
                toast.success("Batas administrasi terdeteksi!");
            } else {
                toast.warning("Titik lokasi tidak berada di dalam poligon wilayah yang terdaftar.");
            }
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Pemeriksaan poligon batas wilayah gagal.");
        } finally {
            setContainmentLoading(false);
        }
    };

    const formatDistance = (meters?: number | null) => {
        if (meters === undefined || meters === null) return "-";
        if (meters >= 1000) {
            return `${(meters / 1000).toFixed(2)} km`;
        }
        return `${meters.toFixed(0)} m`;
    };

    return (
        <Card className={`border shadow-sm flex flex-col ${className}`}>
            <CardHeader className="pb-3 border-b bg-muted/20">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center text-primary">
                            <Compass className="w-5 h-5" />
                        </div>
                        <div>
                            <CardTitle className="text-base font-semibold">
                                Spatial Knowledge Foundation
                            </CardTitle>
                            <CardDescription className="text-xs">
                                PostGIS Spatial Engine &middot; Real GIS Insights
                            </CardDescription>
                        </div>
                    </div>
                    <Badge variant="outline" className="text-xs bg-emerald-500/10 text-emerald-600 border-emerald-500/20">
                        PostGIS Active
                    </Badge>
                </div>
            </CardHeader>

            <CardContent className="p-4 space-y-4 flex-1">
                {/* Location Selection Section */}
                <div className="space-y-2 p-3 bg-muted/40 rounded-lg border">
                    <div className="flex items-center justify-between">
                        <Label className="text-xs font-semibold flex items-center gap-1.5 text-foreground">
                            <Crosshair className="w-3.5 h-3.5 text-primary" /> Koordinat Analisis
                        </Label>
                        <span className="text-[10px] text-muted-foreground italic">
                            Klik peta untuk set titik
                        </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                        <div>
                            <span className="text-[10px] text-muted-foreground block mb-0.5">Latitude (WGS 84)</span>
                            <Input
                                value={lat}
                                onChange={(e) => setLat(e.target.value)}
                                className="h-8 text-xs font-mono"
                                placeholder="0.507100"
                            />
                        </div>
                        <div>
                            <span className="text-[10px] text-muted-foreground block mb-0.5">Longitude (WGS 84)</span>
                            <Input
                                value={lng}
                                onChange={(e) => setLng(e.target.value)}
                                className="h-8 text-xs font-mono"
                                placeholder="101.447800"
                            />
                        </div>
                    </div>

                    <div className="flex items-center justify-between pt-1 gap-2">
                        <Select onValueChange={(val) => {
                            const found = PEKANBARU_PRESETS.find(p => p.name === val);
                            if (found) handleSelectPreset(found);
                        }}>
                            <SelectTrigger className="h-7 text-xs flex-1">
                                <SelectValue placeholder="Pilih preset lokasi Pekanbaru..." />
                            </SelectTrigger>
                            <SelectContent>
                                {PEKANBARU_PRESETS.map((p) => (
                                    <SelectItem key={p.name} value={p.name} className="text-xs">
                                        {p.name}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>

                        <Button size="sm" variant="outline" className="h-7 text-xs px-2" onClick={handleApplyCoords}>
                            Terapkan
                        </Button>
                    </div>
                </div>

                {/* Operations Tabs */}
                <Tabs defaultValue="context" className="w-full">
                    <TabsList className="grid grid-cols-4 w-full h-8 text-xs">
                        <TabsTrigger value="context" className="text-[11px] px-1">Context</TabsTrigger>
                        <TabsTrigger value="nearest" className="text-[11px] px-1">Nearest</TabsTrigger>
                        <TabsTrigger value="radius" className="text-[11px] px-1">Radius</TabsTrigger>
                        <TabsTrigger value="admin" className="text-[11px] px-1">Wilayah</TabsTrigger>
                    </TabsList>

                    {/* TAB 1: SPATIAL CONTEXT */}
                    <TabsContent value="context" className="space-y-3 pt-2">
                        <div className="flex items-center justify-between">
                            <p className="text-xs text-muted-foreground">
                                Ringkasan spasial menyeluruh di sekitar titik target via PostGIS.
                            </p>
                            <Button
                                size="sm"
                                onClick={handleRunSpatialContext}
                                disabled={contextLoading}
                                className="h-8 text-xs"
                            >
                                {contextLoading ? (
                                    <><Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> Menghitung...</>
                                ) : (
                                    <><Sparkles className="w-3.5 h-3.5 mr-1" /> Analisis Lengkap</>
                                )}
                            </Button>
                        </div>

                        {contextResult && (
                            <ScrollArea className="h-[280px] pr-2">
                                <div className="space-y-3 text-xs">
                                    {/* Dataset Access Summary */}
                                    <div className="flex items-center justify-between p-2 rounded bg-muted/30 border text-[11px]">
                                        <span className="text-muted-foreground flex items-center gap-1">
                                            <Layers className="w-3.5 h-3.5" /> Dataset Terotorisasi:
                                        </span>
                                        <Badge variant="secondary" className="text-[10px]">
                                            {contextResult.authorized_datasets?.length || 0} Dataset GIS
                                        </Badge>
                                    </div>

                                    {/* Transportation Context */}
                                    <div className="p-2.5 rounded-lg border bg-card space-y-1.5">
                                        <div className="font-semibold text-xs flex items-center gap-1.5 text-blue-600 dark:text-blue-400">
                                            <Navigation className="w-3.5 h-3.5" /> Akses Jalan & Transportasi
                                        </div>
                                        <div className="grid grid-cols-2 gap-2 pt-1 text-[11px]">
                                            <div className="bg-muted/30 p-1.5 rounded">
                                                <span className="text-muted-foreground block text-[10px]">Jalan Arteri Terdekat</span>
                                                <span className="font-medium">
                                                    {formatDistance(contextResult.transportation?.nearest_arterial_road?.distance_meters)}
                                                </span>
                                            </div>
                                            <div className="bg-muted/30 p-1.5 rounded">
                                                <span className="text-muted-foreground block text-[10px]">Jalan Kolektor</span>
                                                <span className="font-medium">
                                                    {formatDistance(contextResult.transportation?.nearest_collector_road?.distance_meters)}
                                                </span>
                                            </div>
                                            <div className="bg-muted/30 p-1.5 rounded col-span-2">
                                                <span className="text-muted-foreground block text-[10px]">Jalan Lokal Terdekat</span>
                                                <span className="font-medium">
                                                    {formatDistance(contextResult.transportation?.nearest_local_road?.distance_meters)}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Public Facilities */}
                                    <div className="p-2.5 rounded-lg border bg-card space-y-1.5">
                                        <div className="font-semibold text-xs flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400">
                                            <Hospital className="w-3.5 h-3.5" /> Fasilitas Publik & Kesehatan
                                        </div>
                                        <div className="grid grid-cols-2 gap-2 pt-1 text-[11px]">
                                            <div className="bg-muted/30 p-1.5 rounded">
                                                <span className="text-muted-foreground block text-[10px]">RS Terdekat</span>
                                                <span className="font-medium">
                                                    {formatDistance(contextResult.facilities?.nearest_hospital?.distance_meters)}
                                                </span>
                                            </div>
                                            <div className="bg-muted/30 p-1.5 rounded">
                                                <span className="text-muted-foreground block text-[10px]">RS Radius 2 km</span>
                                                <span className="font-medium">
                                                    {contextResult.facilities?.hospitals_within_2km ?? 0} unit
                                                </span>
                                            </div>
                                            <div className="bg-muted/30 p-1.5 rounded">
                                                <span className="text-muted-foreground block text-[10px]">Puskesmas / Klinik</span>
                                                <span className="font-medium">
                                                    {formatDistance(contextResult.facilities?.nearest_clinic?.distance_meters)}
                                                </span>
                                            </div>
                                            <div className="bg-muted/30 p-1.5 rounded">
                                                <span className="text-muted-foreground block text-[10px]">Kantor Polisi</span>
                                                <span className="font-medium">
                                                    {formatDistance(contextResult.facilities?.nearest_police_station?.distance_meters)}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Administrative & Religious */}
                                    <div className="p-2.5 rounded-lg border bg-card space-y-1.5">
                                        <div className="font-semibold text-xs flex items-center gap-1.5 text-purple-600 dark:text-purple-400">
                                            <Building2 className="w-3.5 h-3.5" /> Wilayah & Rumah Ibadah
                                        </div>
                                        <div className="grid grid-cols-2 gap-2 pt-1 text-[11px]">
                                            <div className="bg-muted/30 p-1.5 rounded col-span-2">
                                                <span className="text-muted-foreground block text-[10px]">Kecamatan (Batas Poligon)</span>
                                                <span className="font-medium">
                                                    {contextResult.administrative?.contained_in_area?.properties?.KECAMATAN ||
                                                     contextResult.administrative?.contained_in_area?.properties?.NAMOBJ ||
                                                     contextResult.administrative?.contained_in_area?.area_name ||
                                                     "Terkonfirmasi di Wilayah Pekanbaru"}
                                                </span>
                                            </div>
                                            <div className="bg-muted/30 p-1.5 rounded">
                                                <span className="text-muted-foreground block text-[10px]">Masjid Terdekat</span>
                                                <span className="font-medium">
                                                    {formatDistance(contextResult.religious?.nearest_mosque?.distance_meters)}
                                                </span>
                                            </div>
                                            <div className="bg-muted/30 p-1.5 rounded">
                                                <span className="text-muted-foreground block text-[10px]">Masjid dlm 1 km</span>
                                                <span className="font-medium">
                                                    {contextResult.religious?.mosques_within_1km ?? 0} unit
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Facts List */}
                                    {contextResult.facts && contextResult.facts.length > 0 && (
                                        <div className="p-2 border rounded-md bg-muted/20">
                                            <span className="text-[11px] font-semibold block mb-1">
                                                Fakta Spasial PostGIS ({contextResult.facts.length} entitas):
                                            </span>
                                            <ul className="space-y-1">
                                                {contextResult.facts.slice(0, 8).map((fact, idx) => (
                                                    <li key={idx} className="flex items-center justify-between text-[10px] text-muted-foreground">
                                                        <span>{fact.display_name || fact.subcategory}</span>
                                                        <span className="font-mono text-foreground">
                                                            {fact.distance_meters !== undefined ? `${fact.distance_meters.toFixed(0)}m` : `${fact.count_within_2km || 0} unit`}
                                                        </span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            </ScrollArea>
                        )}
                    </TabsContent>

                    {/* TAB 2: NEAREST FEATURE */}
                    <TabsContent value="nearest" className="space-y-3 pt-2">
                        <div className="space-y-2">
                            <Label className="text-xs">Pilih Kategori Objek Terdekat</Label>
                            <Select value={nearestSubcat} onValueChange={setNearestSubcat}>
                                <SelectTrigger className="h-8 text-xs">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    {DEFAULT_SUBCATEGORIES.map((s) => (
                                        <SelectItem key={s.value} value={s.value} className="text-xs">
                                            {s.label}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>

                            <Button
                                size="sm"
                                className="w-full h-8 text-xs"
                                onClick={handleRunNearest}
                                disabled={nearestLoading}
                            >
                                {nearestLoading ? (
                                    <><Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> Menghitung Jarak Spasial...</>
                                ) : (
                                    <><Search className="w-3.5 h-3.5 mr-1" /> Cari Objek Terdekat (ST_Distance)</>
                                )}
                            </Button>
                        </div>

                        {nearestResult && (
                            <div className="p-3 rounded-lg border bg-card space-y-2 text-xs">
                                <div className="flex items-center justify-between">
                                    <span className="font-semibold text-foreground">
                                        {nearestResult.display_name || nearestResult.subcategory}
                                    </span>
                                    <Badge variant="secondary" className="font-mono text-xs">
                                        {formatDistance(nearestResult.distance_meters)}
                                    </Badge>
                                </div>
                                <Separator />
                                <div className="space-y-1 text-[11px] text-muted-foreground">
                                    <p><strong>Feature ID:</strong> <span className="font-mono">{nearestResult.feature_id}</span></p>
                                    {nearestResult.properties && Object.keys(nearestResult.properties).length > 0 && (
                                        <div className="mt-1 bg-muted/40 p-2 rounded">
                                            <span className="font-semibold block text-[10px] mb-1">Atribut GIS:</span>
                                            {Object.entries(nearestResult.properties).slice(0, 5).map(([k, v]) => (
                                                <div key={k} className="flex justify-between py-0.5">
                                                    <span className="text-[10px] text-muted-foreground">{k}:</span>
                                                    <span className="text-[10px] font-mono">{String(v)}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </TabsContent>

                    {/* TAB 3: RADIUS SEARCH */}
                    <TabsContent value="radius" className="space-y-3 pt-2">
                        <div className="space-y-2">
                            <Label className="text-xs">Kategori Objek</Label>
                            <Select value={radiusSubcat} onValueChange={setRadiusSubcat}>
                                <SelectTrigger className="h-8 text-xs">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    {DEFAULT_SUBCATEGORIES.map((s) => (
                                        <SelectItem key={s.value} value={s.value} className="text-xs">
                                            {s.label}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>

                            <div className="space-y-1 pt-1">
                                <div className="flex justify-between text-xs">
                                    <span>Radius Pencarian:</span>
                                    <span className="font-mono font-bold text-primary">{radiusMeters} meter</span>
                                </div>
                                <Slider
                                    value={[radiusMeters]}
                                    min={250}
                                    max={10000}
                                    step={250}
                                    onValueChange={(vals) => setRadiusMeters(vals[0])}
                                />
                            </div>

                            <Button
                                size="sm"
                                className="w-full h-8 text-xs mt-2"
                                onClick={handleRunRadius}
                                disabled={radiusLoading}
                            >
                                {radiusLoading ? (
                                    <><Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> Menganalisis Buffer...</>
                                ) : (
                                    <><Search className="w-3.5 h-3.5 mr-1" /> Cari Dalam Radius (ST_DWithin)</>
                                )}
                            </Button>
                        </div>

                        {radiusResult && (
                            <div className="space-y-2 text-xs">
                                <div className="flex items-center justify-between p-2 rounded bg-muted/40 border">
                                    <span className="text-muted-foreground">Jumlah Ditemukan:</span>
                                    <Badge variant="outline" className="font-bold">
                                        {radiusResult.count} Objek Spasial
                                    </Badge>
                                </div>

                                <ScrollArea className="h-[180px]">
                                    <div className="space-y-1.5 pr-2">
                                        {radiusResult.features.map((f, i) => (
                                            <div key={i} className="p-2 border rounded bg-card text-[11px] flex justify-between items-center">
                                                <div>
                                                    <span className="font-medium block">
                                                        {f.display_name || `Feature #${i + 1}`}
                                                    </span>
                                                    <span className="text-[10px] text-muted-foreground">
                                                        ID: {f.feature_id}
                                                    </span>
                                                </div>
                                                <Badge variant="secondary" className="font-mono text-[10px]">
                                                    {formatDistance(f.distance_meters)}
                                                </Badge>
                                            </div>
                                        ))}
                                    </div>
                                </ScrollArea>
                            </div>
                        )}
                    </TabsContent>

                    {/* TAB 4: ADMINISTRATIVE BOUNDARY */}
                    <TabsContent value="admin" className="space-y-3 pt-2">
                        <p className="text-xs text-muted-foreground">
                            Pemeriksaan poligon batas administrasi (ST_Contains) untuk memastikan lokasi berada di dalam yurisdiksi wilayah Pekanbaru.
                        </p>

                        <Button
                            size="sm"
                            className="w-full h-8 text-xs"
                            onClick={handleRunContainment}
                            disabled={containmentLoading}
                        >
                            {containmentLoading ? (
                                <><Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> Memeriksa Poligon...</>
                            ) : (
                                <><Building2 className="w-3.5 h-3.5 mr-1" /> Cek Batas Administrasi (ST_Contains)</>
                            )}
                        </Button>

                        {containmentResult && (
                            <div className="p-3 rounded-lg border bg-card space-y-2 text-xs">
                                <div className="flex items-center gap-1.5 text-emerald-600 font-semibold">
                                    <CheckCircle2 className="w-4 h-4" /> Lokasi Terkonfirmasi Dalam Batas Wilayah
                                </div>
                                <div className="space-y-1 text-[11px] bg-muted/30 p-2 rounded">
                                    {Object.entries(containmentResult.properties || {}).slice(0, 6).map(([k, v]) => (
                                        <div key={k} className="flex justify-between py-0.5">
                                            <span className="text-muted-foreground">{k}:</span>
                                            <span className="font-medium font-mono">{String(v)}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </TabsContent>
                </Tabs>
            </CardContent>
        </Card>
    );
}

export default SpatialAnalysisPanel;
