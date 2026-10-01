"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import {
    ShieldCheck, Building2, Database, Plus, Ban,
    CheckCircle2, Search, RefreshCw, Layers, Clock,
    Sparkles, AlertCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { toast } from "sonner";
import { GISAccessService, type GISAccessGrant, type GISAccessWorkspaceInfo, type GISAccessDatasetInfo } from "@/lib/api/GISAccessService";

export default function GISAccessManagementPage() {
    const [grants, setGrants] = useState<GISAccessGrant[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");
    const [statusFilter, setStatusFilter] = useState<"all" | "active" | "revoked">("all");
    const [isGrantModalOpen, setIsGrantModalOpen] = useState(false);
    const [availableWorkspaces, setAvailableWorkspaces] = useState<GISAccessWorkspaceInfo[]>([]);
    const [availableDatasets, setAvailableDatasets] = useState<GISAccessDatasetInfo[]>([]);
    const [selectedWorkspaceId, setSelectedWorkspaceId] = useState("");
    const [selectedDatasetId, setSelectedDatasetId] = useState("");
    const [grantNotes, setGrantNotes] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [grantToRevoke, setGrantToRevoke] = useState<GISAccessGrant | null>(null);
    const [revokeReason, setRevokeReason] = useState("");
    const [isRevoking, setIsRevoking] = useState(false);

    const fetchGrants = useCallback(async () => {
        try {
            setLoading(true);
            const res = await GISAccessService.listAllGrants({ limit: 200 });
            setGrants(res.items || []);
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Gagal memuat daftar akses GIS");
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchDropdownData = useCallback(async () => {
        try {
            const [workspaces, datasets] = await Promise.all([
                GISAccessService.getWorkspacesForGrant(),
                GISAccessService.getDatasetsForGrant(),
            ]);
            setAvailableWorkspaces(workspaces || []);
            setAvailableDatasets(datasets || []);
        } catch (err) {
            console.error("Error loading dropdown data:", err);
        }
    }, []);

    useEffect(() => {
        fetchGrants();
        fetchDropdownData();
    }, [fetchGrants, fetchDropdownData]);

    const handleGrantAccess = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedWorkspaceId || !selectedDatasetId) {
            toast.warning("Silakan pilih Ruang Kerja dan GIS Dataset");
            return;
        }
        try {
            setIsSubmitting(true);
            await GISAccessService.grantAccess({
                workspace_id: selectedWorkspaceId,
                dataset_id: selectedDatasetId,
                notes: grantNotes.trim() || undefined,
            });
            toast.success("Akses GIS berhasil diberikan ke Ruang Kerja!");
            setIsGrantModalOpen(false);
            setSelectedWorkspaceId("");
            setSelectedDatasetId("");
            setGrantNotes("");
            fetchGrants();
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Gagal memberikan akses GIS");
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleRevokeConfirm = async () => {
        if (!grantToRevoke) return;
        try {
            setIsRevoking(true);
            await GISAccessService.revokeAccess({
                workspace_id: grantToRevoke.workspace_id,
                dataset_id: grantToRevoke.dataset_id,
                reason: revokeReason.trim() || undefined,
            });
            toast.success("Akses GIS berhasil dicabut. Dataset GIS tetap aman.");
            setGrantToRevoke(null);
            setRevokeReason("");
            fetchGrants();
        } catch (err: any) {
            toast.error(err?.response?.data?.detail || "Gagal mencabut akses GIS");
        } finally {
            setIsRevoking(false);
        }
    };

    const filteredGrants = useMemo(() => {
        return grants.filter((grant) => {
            const matchesSearch =
                (grant.workspace?.name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
                (grant.dataset?.name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
                (grant.granter?.email || "").toLowerCase().includes(searchTerm.toLowerCase());
            if (!matchesSearch) return false;
            if (statusFilter === "active") return grant.is_active;
            if (statusFilter === "revoked") return !grant.is_active;
            return true;
        });
    }, [grants, searchTerm, statusFilter]);

    const activeCount = useMemo(() => grants.filter((g) => g.is_active).length, [grants]);
    const revokedCount = useMemo(() => grants.filter((g) => !g.is_active).length, [grants]);
    const uniqueWorkspacesCount = useMemo(
        () => new Set(grants.filter((g) => g.is_active).map((g) => g.workspace_id)).size,
        [grants]
    );

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b pb-5">
                <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-lg bg-primary/10 text-primary">
                        <ShieldCheck className="h-6 w-6" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">Kelola Akses GIS</h1>
                        <p className="text-sm text-muted-foreground mt-0.5">
                            Atur hak akses platform GIS Dataset ke Ruang Kerja Developer.
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2.5">
                    <Button variant="outline" size="sm" onClick={() => fetchGrants()} disabled={loading} className="h-9 gap-1.5">
                        <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                        Segarkan
                    </Button>
                    <Button onClick={() => { setSelectedWorkspaceId(""); setSelectedDatasetId(""); setGrantNotes(""); setIsGrantModalOpen(true); }}
                        size="sm" className="h-9 gap-1.5">
                        <Plus className="h-4 w-4" /> Beri Akses Baru
                    </Button>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Card className="border-l-4 border-l-emerald-500 shadow-sm">
                    <CardHeader className="pb-2">
                        <CardDescription className="text-xs font-medium uppercase tracking-wider">Akses Aktif</CardDescription>
                        <CardTitle className="text-2xl font-bold flex items-center justify-between">
                            <span>{activeCount}</span>
                            <CheckCircle2 className="h-5 w-5 text-emerald-500 opacity-80" />
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="text-xs text-muted-foreground pt-0">Entitlement GIS aktif dan siap digunakan</CardContent>
                </Card>
                <Card className="border-l-4 border-l-blue-500 shadow-sm">
                    <CardHeader className="pb-2">
                        <CardDescription className="text-xs font-medium uppercase tracking-wider">Workspace Terhubung</CardDescription>
                        <CardTitle className="text-2xl font-bold flex items-center justify-between">
                            <span>{uniqueWorkspacesCount}</span>
                            <Building2 className="h-5 w-5 text-blue-500 opacity-80" />
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="text-xs text-muted-foreground pt-0">Tenant dengan akses GIS terverifikasi</CardContent>
                </Card>
                <Card className="border-l-4 border-l-amber-500 shadow-sm">
                    <CardHeader className="pb-2">
                        <CardDescription className="text-xs font-medium uppercase tracking-wider">Akses Dicabut</CardDescription>
                        <CardTitle className="text-2xl font-bold flex items-center justify-between">
                            <span>{revokedCount}</span>
                            <Ban className="h-5 w-5 text-amber-500 opacity-80" />
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="text-xs text-muted-foreground pt-0">Akses non-aktif (dataset tetap utuh)</CardContent>
                </Card>
            </div>

            {/* Table Section */}
            <Card className="shadow-sm border">
                <CardHeader className="pb-3">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                        <div>
                            <CardTitle className="text-base font-semibold">Daftar Hibah Akses GIS</CardTitle>
                            <CardDescription className="text-xs">Riwayat pemberian dan pencabutan hak akses dataset per workspace.</CardDescription>
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                            <div className="relative w-64">
                                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                                <Input placeholder="Cari workspace / dataset..." value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)} className="pl-8 h-9 text-xs" />
                            </div>
                            <div className="flex items-center rounded-md border bg-muted/40 p-0.5 text-xs font-medium">
                                {(["all", "active", "revoked"] as const).map((f) => (
                                    <button key={f} type="button" onClick={() => setStatusFilter(f)}
                                        className={`px-2.5 py-1 rounded-sm transition-all ${statusFilter === f ? "bg-background shadow-sm text-foreground font-semibold" : "text-muted-foreground hover:text-foreground"}`}>
                                        {f === "all" ? "Semua" : f === "active" ? "Aktif" : "Dicabut"}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="p-0">
                    <div className="overflow-x-auto">
                        <Table>
                            <TableHeader className="bg-muted/40">
                                <TableRow>
                                    <TableHead className="w-[220px]">Ruang Kerja</TableHead>
                                    <TableHead>GIS Dataset</TableHead>
                                    <TableHead>Diberikan Oleh</TableHead>
                                    <TableHead>Waktu</TableHead>
                                    <TableHead className="w-[110px]">Status</TableHead>
                                    <TableHead className="text-right w-[140px]">Tindakan</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {loading ? (
                                    <TableRow>
                                        <TableCell colSpan={6} className="text-center py-10">
                                            <div className="flex flex-col items-center gap-2">
                                                <RefreshCw className="h-6 w-6 animate-spin text-primary" />
                                                <span className="text-xs text-muted-foreground">Memuat data akses GIS...</span>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ) : filteredGrants.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={6} className="text-center py-12">
                                            <div className="flex flex-col items-center gap-2 text-muted-foreground">
                                                <ShieldCheck className="h-10 w-10 opacity-20" />
                                                <p className="font-medium text-sm text-foreground">Tidak ada data akses GIS</p>
                                                <p className="text-xs">{searchTerm ? "Tidak ada hasil yang cocok." : "Klik 'Beri Akses Baru' untuk memulai."}</p>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ) : filteredGrants.map((grant) => (
                                    <TableRow key={grant.id} className="hover:bg-muted/30 transition-colors">
                                        <TableCell>
                                            <div className="flex items-center gap-2.5">
                                                <div className="p-1.5 rounded-md bg-blue-500/10 text-blue-600 shrink-0">
                                                    <Building2 className="h-4 w-4" />
                                                </div>
                                                <div className="min-w-0">
                                                    <div className="font-medium text-sm truncate">{grant.workspace?.name || "—"}</div>
                                                    <div className="text-xs text-muted-foreground truncate">{grant.workspace?.slug}</div>
                                                </div>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2.5">
                                                <div className="p-1.5 rounded-md bg-emerald-500/10 text-emerald-600 shrink-0">
                                                    <Database className="h-4 w-4" />
                                                </div>
                                                <div className="min-w-0">
                                                    <div className="font-medium text-sm truncate">{grant.dataset?.name || "—"}</div>
                                                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-0.5">
                                                        <Layers className="h-3 w-3" />
                                                        {grant.dataset?.total_layers || 0} layer
                                                        <span className="text-[10px] px-1 bg-muted rounded font-mono uppercase">{grant.dataset?.file_type}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="text-xs">
                                                <div className="font-medium">{grant.granter?.name || grant.granter?.email || "Admin"}</div>
                                                {grant.notes && <div className="text-muted-foreground italic text-[11px] truncate max-w-[160px]">{grant.notes}</div>}
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <div className="text-xs text-muted-foreground">
                                                <div className="flex items-center gap-1">
                                                    <Clock className="h-3 w-3" />
                                                    {new Date(grant.granted_at).toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" })}
                                                </div>
                                                {!grant.is_active && grant.revoked_at && (
                                                    <div className="text-amber-600 text-[11px] mt-0.5">
                                                        Dicabut: {new Date(grant.revoked_at).toLocaleDateString("id-ID")}
                                                    </div>
                                                )}
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            {grant.is_active ? (
                                                <Badge variant="outline" className="bg-emerald-500/10 text-emerald-600 border-emerald-500/20 text-xs gap-1">
                                                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" /> Aktif
                                                </Badge>
                                            ) : (
                                                <Badge variant="outline" className="bg-amber-500/10 text-amber-600 border-amber-500/20 text-xs gap-1">
                                                    <span className="h-1.5 w-1.5 rounded-full bg-amber-500" /> Dicabut
                                                </Badge>
                                            )}
                                        </TableCell>
                                        <TableCell className="text-right">
                                            {grant.is_active ? (
                                                <Button variant="ghost" size="sm" onClick={() => setGrantToRevoke(grant)}
                                                    className="h-8 px-2.5 text-xs text-destructive hover:bg-destructive/10 gap-1">
                                                    <Ban className="h-3.5 w-3.5" /> Cabut
                                                </Button>
                                            ) : (
                                                <Button variant="ghost" size="sm" onClick={async () => {
                                                    try {
                                                        await GISAccessService.grantAccess({ workspace_id: grant.workspace_id, dataset_id: grant.dataset_id, notes: "Re-activated by admin" });
                                                        toast.success("Akses berhasil diaktifkan kembali!");
                                                        fetchGrants();
                                                    } catch (err: any) { toast.error(err?.response?.data?.detail || "Gagal"); }
                                                }} className="h-8 px-2.5 text-xs text-primary hover:bg-primary/10 gap-1">
                                                    <CheckCircle2 className="h-3.5 w-3.5" /> Pulihkan
                                                </Button>
                                            )}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </div>
                </CardContent>
            </Card>

            {/* Grant Modal */}
            <Dialog open={isGrantModalOpen} onOpenChange={setIsGrantModalOpen}>
                <DialogContent className="sm:max-w-[480px]">
                    <form onSubmit={handleGrantAccess}>
                        <DialogHeader>
                            <DialogTitle className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-primary" />Berikan Akses Dataset GIS</DialogTitle>
                            <DialogDescription className="text-xs">Pilih Ruang Kerja Developer dan Platform Dataset GIS yang akan diberikan sebagai entitlement.</DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                            <div className="space-y-1.5">
                                <label className="text-xs font-semibold flex items-center gap-1.5"><Building2 className="h-3.5 w-3.5 text-blue-500" />Pilih Ruang Kerja *</label>
                                <Select value={selectedWorkspaceId} onValueChange={setSelectedWorkspaceId}>
                                    <SelectTrigger className="h-9 text-xs"><SelectValue placeholder="-- Pilih Workspace Developer --" /></SelectTrigger>
                                    <SelectContent>
                                        {availableWorkspaces.map((ws) => (
                                            <SelectItem key={ws.id} value={ws.id} className="text-xs">{ws.name} ({ws.slug})</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-xs font-semibold flex items-center gap-1.5"><Database className="h-3.5 w-3.5 text-emerald-500" />Pilih Dataset GIS *</label>
                                <Select value={selectedDatasetId} onValueChange={setSelectedDatasetId}>
                                    <SelectTrigger className="h-9 text-xs"><SelectValue placeholder="-- Pilih Dataset GIS --" /></SelectTrigger>
                                    <SelectContent>
                                        {availableDatasets.map((ds) => (
                                            <SelectItem key={ds.id} value={ds.id} className="text-xs">{ds.name} ({ds.total_layers} layer)</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-1.5">
                                <label className="text-xs font-semibold">Catatan Administratif (Opsional)</label>
                                <Textarea placeholder="Catatan untuk pemberian akses ini..." value={grantNotes} onChange={(e) => setGrantNotes(e.target.value)} rows={2} className="text-xs resize-none" />
                            </div>
                            <div className="p-3 rounded-md bg-muted/50 border text-xs text-muted-foreground flex gap-2">
                                <Sparkles className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                                <span>Setelah diberikan, seluruh anggota workspace dapat menggunakan dataset ini pada proyek GIS mereka.</span>
                            </div>
                        </div>
                        <DialogFooter className="gap-2 sm:gap-0">
                            <Button type="button" variant="outline" size="sm" onClick={() => setIsGrantModalOpen(false)} disabled={isSubmitting}>Batal</Button>
                            <Button type="submit" size="sm" disabled={isSubmitting || !selectedWorkspaceId || !selectedDatasetId} className="gap-1.5">
                                {isSubmitting ? <><RefreshCw className="h-3.5 w-3.5 animate-spin" /> Menyimpan...</> : <><ShieldCheck className="h-3.5 w-3.5" /> Berikan Akses</>}
                            </Button>
                        </DialogFooter>
                    </form>
                </DialogContent>
            </Dialog>

            {/* Revoke Confirmation */}
            <AlertDialog open={!!grantToRevoke} onOpenChange={(open) => !open && setGrantToRevoke(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle className="flex items-center gap-2 text-destructive">
                            <AlertCircle className="h-5 w-5" /> Konfirmasi Pencabutan Akses GIS
                        </AlertDialogTitle>
                        <AlertDialogDescription className="space-y-2 text-xs">
                            <p>Anda akan mencabut hak akses <strong>{grantToRevoke?.dataset?.name}</strong> dari workspace <strong>{grantToRevoke?.workspace?.name}</strong>.</p>
                            <p className="font-semibold text-foreground">Catatan Penting:</p>
                            <ul className="list-disc list-inside space-y-1">
                                <li>Dataset GIS platform <strong>TIDAK AKAN DIHAPUS</strong> dan tetap utuh.</li>
                                <li>Anggota workspace tidak lagi dapat menambahkan layer dari dataset ini.</li>
                            </ul>
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <div className="my-2 space-y-1.5">
                        <label className="text-xs font-semibold">Alasan Pencabutan (Opsional)</label>
                        <Input placeholder="Contoh: Periode berakhir" value={revokeReason} onChange={(e) => setRevokeReason(e.target.value)} className="text-xs h-8" />
                    </div>
                    <AlertDialogFooter>
                        <AlertDialogCancel disabled={isRevoking}>Batal</AlertDialogCancel>
                        <AlertDialogAction onClick={handleRevokeConfirm} disabled={isRevoking}
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90 text-xs">
                            {isRevoking ? "Mencabut..." : "Ya, Cabut Akses"}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
