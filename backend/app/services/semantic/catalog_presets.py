"""
Catalog Presets for Pekanbaru GIS Layers.

Maps known technical layer names to semantic definitions.
This seeder is idempotent — safe to run multiple times.
New cities (Jakarta, Bandung, etc.) will register their own
layer→semantic mappings without touching this file.
"""
from typing import List, Dict, Any

# Canonical layer name → semantic definition
# layer_name_pattern: matched case-insensitively against GISLayer.name
PEKANBARU_CATALOG: List[Dict[str, Any]] = [
    # ── TRANSPORTATION ──────────────────────────────────────────────────────
    {
        "name_pattern": "JalanArteri",
        "category": "transportation",
        "subcategory": "arterial_road",
        "display_name": "Jalan Arteri",
        "description": "Jalan arteri utama Kota Pekanbaru",
        "semantic_metadata": {
            "aliases": ["jalan arteri", "jalan utama", "arterial road", "main road"],
            "capabilities": ["distance", "nearest", "intersects"],
            "geometry_type": "LineString",
        },
    },
    {
        "name_pattern": "JalanKolektor",
        "category": "transportation",
        "subcategory": "collector_road",
        "display_name": "Jalan Kolektor",
        "description": "Jalan kolektor Kota Pekanbaru",
        "semantic_metadata": {
            "aliases": ["jalan kolektor", "jalan penghubung", "collector road"],
            "capabilities": ["distance", "nearest", "intersects"],
            "geometry_type": "LineString",
        },
    },
    {
        "name_pattern": "JalanLokal",
        "category": "transportation",
        "subcategory": "local_road",
        "display_name": "Jalan Lokal",
        "description": "Jalan lokal dan lingkungan Kota Pekanbaru",
        "semantic_metadata": {
            "aliases": ["jalan lokal", "jalan lingkungan", "local road"],
            "capabilities": ["distance", "nearest", "intersects"],
            "geometry_type": "LineString",
        },
    },
    {
        "name_pattern": "JalanLain",
        "category": "transportation",
        "subcategory": "other_road",
        "display_name": "Jalan Lain",
        "description": "Jalan lain-lain Kota Pekanbaru",
        "semantic_metadata": {
            "aliases": ["jalan lain", "other road"],
            "capabilities": ["distance", "nearest"],
            "geometry_type": "LineString",
        },
    },
    # ── PUBLIC FACILITY ─────────────────────────────────────────────────────
    {
        "name_pattern": "RumahSakit",
        "category": "public_facility",
        "subcategory": "hospital",
        "display_name": "Rumah Sakit",
        "description": "Rumah sakit di Kota Pekanbaru",
        "semantic_metadata": {
            "aliases": ["rumah sakit", "rs", "hospital", "rsud", "rsu"],
            "capabilities": ["count", "nearest", "distance", "within_radius"],
            "geometry_type": "Point",
        },
    },
    {
        "name_pattern": "PUSKESMAS",
        "category": "public_facility",
        "subcategory": "puskesmas",
        "display_name": "Puskesmas",
        "description": "Pusat kesehatan masyarakat di Kota Pekanbaru",
        "semantic_metadata": {
            "aliases": ["puskesmas", "puskemas", "klinik", "clinic", "health center"],
            "capabilities": ["count", "nearest", "distance", "within_radius"],
            "geometry_type": "Point",
        },
    },
    {
        "name_pattern": "KantorPolisi",
        "category": "public_facility",
        "subcategory": "police_station",
        "display_name": "Kantor Polisi",
        "description": "Kantor polisi di Kota Pekanbaru",
        "semantic_metadata": {
            "aliases": ["kantor polisi", "polsek", "polres", "polda", "police station"],
            "capabilities": ["count", "nearest", "distance", "within_radius"],
            "geometry_type": "Point",
        },
    },
    {
        "name_pattern": "TNI",
        "category": "public_facility",
        "subcategory": "military",
        "display_name": "Fasilitas TNI",
        "description": "Fasilitas militer / TNI di Kota Pekanbaru",
        "semantic_metadata": {
            "aliases": ["tni", "militer", "military", "kodam", "korem"],
            "capabilities": ["count", "nearest", "distance"],
            "geometry_type": "Point",
        },
    },
    {
        "name_pattern": "KantorGubernur",
        "category": "public_facility",
        "subcategory": "governor_office",
        "display_name": "Kantor Gubernur",
        "description": "Kantor gubernur Provinsi Riau",
        "semantic_metadata": {
            "aliases": ["kantor gubernur", "governor office"],
            "capabilities": ["nearest", "distance"],
            "geometry_type": "Point",
        },
    },
    {
        "name_pattern": "KantorWalikota",
        "category": "public_facility",
        "subcategory": "city_hall",
        "display_name": "Kantor Walikota",
        "description": "Balai kota / kantor walikota Pekanbaru",
        "semantic_metadata": {
            "aliases": ["kantor walikota", "balai kota", "city hall"],
            "capabilities": ["nearest", "distance"],
            "geometry_type": "Point",
        },
    },
    {
        "name_pattern": "KantorCamat",
        "category": "public_facility",
        "subcategory": "district_office",
        "display_name": "Kantor Camat",
        "description": "Kantor kecamatan di Kota Pekanbaru",
        "semantic_metadata": {
            "aliases": ["kantor camat", "kecamatan", "district office"],
            "capabilities": ["count", "nearest", "distance", "within_radius"],
            "geometry_type": "Point",
        },
    },
    {
        "name_pattern": "KantorLurah",
        "category": "public_facility",
        "subcategory": "village_office",
        "display_name": "Kantor Lurah",
        "description": "Kantor kelurahan di Kota Pekanbaru",
        "semantic_metadata": {
            "aliases": ["kantor lurah", "kelurahan", "village office"],
            "capabilities": ["count", "nearest", "distance", "within_radius"],
            "geometry_type": "Point",
        },
    },
    {
        "name_pattern": "KantorKades",
        "category": "public_facility",
        "subcategory": "village_office",
        "display_name": "Kantor Kepala Desa",
        "description": "Kantor kepala desa di wilayah Pekanbaru",
        "semantic_metadata": {
            "aliases": ["kantor kades", "kantor desa", "kepala desa", "village head office"],
            "capabilities": ["count", "nearest", "distance"],
            "geometry_type": "Point",
        },
    },
    # ── RELIGIOUS ────────────────────────────────────────────────────────────
    {
        "name_pattern": "Mesjid",
        "category": "religious",
        "subcategory": "mosque",
        "display_name": "Masjid",
        "description": "Masjid di Kota Pekanbaru",
        "semantic_metadata": {
            "aliases": ["masjid", "mesjid", "mushola", "mosque"],
            "capabilities": ["count", "nearest", "distance", "within_radius"],
            "geometry_type": "Point",
        },
    },
    {
        "name_pattern": "Gereja",
        "category": "religious",
        "subcategory": "church",
        "display_name": "Gereja",
        "description": "Gereja di Kota Pekanbaru",
        "semantic_metadata": {
            "aliases": ["gereja", "church"],
            "capabilities": ["count", "nearest", "distance", "within_radius"],
            "geometry_type": "Point",
        },
    },
    {
        "name_pattern": "Vihara",
        "category": "religious",
        "subcategory": "vihara",
        "display_name": "Vihara",
        "description": "Vihara di Kota Pekanbaru",
        "semantic_metadata": {
            "aliases": ["vihara", "kuil", "temple"],
            "capabilities": ["count", "nearest", "distance"],
            "geometry_type": "Point",
        },
    },
    {
        "name_pattern": "IbadahLainnya",
        "category": "religious",
        "subcategory": "other_place_of_worship",
        "display_name": "Tempat Ibadah Lainnya",
        "description": "Tempat ibadah lainnya di Kota Pekanbaru",
        "semantic_metadata": {
            "aliases": ["tempat ibadah", "ibadah lainnya", "place of worship"],
            "capabilities": ["count", "nearest", "distance"],
            "geometry_type": "Point",
        },
    },
    # ── COMMERCIAL ───────────────────────────────────────────────────────────
    {
        "name_pattern": "Niaga",
        "category": "commercial",
        "subcategory": "commercial_area",
        "display_name": "Lokasi Niaga",
        "description": "Area perdagangan dan niaga di Kota Pekanbaru",
        "semantic_metadata": {
            "aliases": ["niaga", "komersial", "perdagangan", "pasar", "commercial", "trade"],
            "capabilities": ["count", "nearest", "distance", "within_radius"],
            "geometry_type": "Point",
        },
    },
    # ── TRANSPORTATION INFRASTRUCTURE ────────────────────────────────────────
    {
        "name_pattern": "Pelabuhan",
        "category": "transportation_infrastructure",
        "subcategory": "port",
        "display_name": "Pelabuhan",
        "description": "Pelabuhan di Kota Pekanbaru",
        "semantic_metadata": {
            "aliases": ["pelabuhan", "dermaga", "port", "harbor"],
            "capabilities": ["nearest", "distance"],
            "geometry_type": "Point",
        },
    },
    # ── ADMINISTRATIVE ────────────────────────────────────────────────────────
    {
        "name_pattern": "BatasAdministrasi",
        "category": "administrative",
        "subcategory": "administrative_boundary",
        "display_name": "Batas Administrasi",
        "description": "Batas administrasi wilayah Kota Pekanbaru",
        "semantic_metadata": {
            "aliases": ["batas administrasi", "batas wilayah", "kecamatan", "administrative boundary"],
            "capabilities": ["contains", "intersects", "boundary"],
            "geometry_type": "Polygon",
        },
    },
]
