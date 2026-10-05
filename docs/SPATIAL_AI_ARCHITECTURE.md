# ScapeGIS — Spatial AI Architecture & Tool Contract (Module 2A)

## 1. Executive Summary

Module 2A defines the deterministic, secure, and auditable bridge between natural language reasoning (future LLM / Gemini) and the ScapeGIS PostGIS spatial foundation (Module 1).

### Core Principle: The Ground Truth Boundary
> **LLM is responsible for intent, reasoning, and synthesis.**  
> **Backend PostGIS services are strictly responsible for ground truth, geometric calculation, and authorization.**

Under no circumstances is an LLM allowed to execute arbitrary SQL, directly query database tables, or invent geometric measurements (distances, areas, coordinates).

---

## 2. Spatial AI Architecture Diagram

```
+-------------------------------------------------------------+
|                     Natural Language User                   |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                 Gemini / LLM Agent (Module 2B)             |
|   - Analyzes user intent                                    |
|   - Selects structured spatial tool                         |
|   - Provides semantic parameters                            |
+-------------------------------------------------------------+
                              |
                     Function Call Contract
                              |
                              v
+=============================================================+
|             ScapeGIS Spatial AI Layer (Module 2A)           |
|                                                             |
|   +-----------------------+     +-----------------------+   |
|   | SpatialAIToolRegistry |<--->|   SpatialAIContext    |   |
|   +-----------------------+     +-----------------------+   |
|               |                             |               |
|               +-------------+---------------+               |
|                             |                               |
|               [Authorization & Scope Chain]                 |
|               User -> Workspace -> Project -> Dataset       |
|                             |                               |
|   +-----------------------------------------------------+   |
|   |                  BaseSpatialTool                    |   |
|   |  - get_spatial_context                              |   |
|   |  - find_nearest                                     |   |
|   |  - search_radius                                    |   |
|   |  - check_containment                                |   |
|   |  - find_intersections                               |   |
|   +-----------------------------------------------------+   |
+=============================================================+
                              |
                  Internal Service Calls Only
                              |
                              v
+-------------------------------------------------------------+
|                  Verified Backend Services                  |
|   - spatial_analysis_service                                |
|   - spatial_context_service                                 |
|   - semantic_service                                        |
+-------------------------------------------------------------+
                              |
                     SQLAlchemy / PostGIS
                              |
                              v
+-------------------------------------------------------------+
|                 PostGIS / PostgreSQL Engine                 |
|   - ST_DWithin / ST_Distance                                |
|   - ST_Contains / ST_Intersects                             |
|   - Spatial Indexes (GIST)                                  |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                      Structured Output                      |
|   - SpatialProvenance (Dataset ID, Layer ID, PostGIS OP)    |
|   - Ground Truth Facts (Exact distances in meters/km)       |
|   - MapAction Events (Highlight, fitBounds, markers)        |
+-------------------------------------------------------------+
```

---

## 3. Tool Registry (`SpatialAIToolRegistry`)

The `SpatialAIToolRegistry` is a singleton repository containing all approved spatial operations callable by an AI agent.

### Capabilities:
- **Registration & Discovery**: Dynamic registration of tool classes conforming to `BaseSpatialTool`.
- **Export to Gemini**: Automatically derives Google Gemini `FunctionDeclaration` objects directly from Pydantic schemas via `to_gemini_declarations()`.
- **Export to OpenAI**: Generates standard JSON-Schema format via `to_json_schemas()`.
- **Safe Execution**: Dispatches tool execution with mandatory `db: Session` and `user: User` injected by backend auth middleware.

---

## 4. Controlled Spatial Tools (5 Standard Tools)

| Tool Name | PostGIS Operation | Input Schema | Output Schema | Purpose |
|---|---|---|---|---|
| `get_spatial_context` | Multi-domain aggregation | `GetSpatialContextInput` | `GetSpatialContextOutput` | Full spatial intelligence snapshot across all 5 domains (transport, health, worship, commercial, admin). |
| `find_nearest` | `ST_Distance`, `ORDER BY geom <-> point` | `FindNearestInput` | `FindNearestOutput` | Locate nearest single POI (hospital, school, arterial road) with exact distance in meters and km. |
| `search_radius` | `ST_DWithin` | `SearchRadiusInput` | `SearchRadiusOutput` | Find all features within a specified radius (up to 50 km) sorted by distance. |
| `check_containment` | `ST_Contains` | `CheckContainmentInput` | `CheckContainmentOutput` | Determine which administrative boundary polygon (kecamatan/kelurahan) contains the coordinate. |
| `find_intersections` | `ST_Intersects` | `FindIntersectionsInput` | `FindIntersectionsOutput` | Identify roads or linear corridors intersecting a buffer zone around the coordinate. |

---

## 5. Authorization Chain Enforcement

Every tool execution enforces a strict multi-tenant authorization hierarchy:

```
[Authenticated User]
        │
        ▼ (Must be member of workspace or platform superuser)
[Workspace Membership]
        │
        ▼ (Project must belong strictly to this workspace)
[Project Scope]
        │
        ▼ (Workspace must have active WorkspaceGISAccess record)
[Authorized GIS Datasets]
        │
        ▼ (Target layer must belong to authorized dataset)
[Semantic GIS Layer]
```

If any check in this chain fails:
- The system raises `SpatialAIAuthorizationError`.
- No PostGIS query is performed.
- Unauthorized data is never leaked or disclosed in error messages.

---

## 6. SpatialAIContext Design

Before an LLM call occurs, `build_spatial_ai_context(db, user, workspace_id, project_id)` constructs a deterministic state snapshot containing:
- Authenticated user ID and workspace metadata.
- Project details (city, province, project type).
- List of authorized GIS datasets.
- Semantic concepts available for AI queries (with category, aliases, and operational capabilities).
- Available tools in registry.

### Token-Optimized System Prompt:
The `to_system_prompt_summary()` method creates a compact (<400 tokens) prompt string that instructs the LLM on exactly which spatial layers exist in this tenant's workspace and strictly enforces tool usage over hallucination.

---

## 7. Provenance & Hallucination Prevention

Every tool output returns `SpatialProvenance` metadata:
```json
{
  "dataset_id": "adb542a8-4c47-413f-a98b-3592b7f7ef00",
  "dataset_name": "Pekanbaru GIS",
  "layer_id": "c71a39df-419b-4394-9b57-a4ad923abebf",
  "layer_name": "Rumah Sakit",
  "semantic_category": "public_facility",
  "semantic_subcategory": "hospital",
  "operation": "ST_Distance",
  "feature_count_queried": 1
}
```

### Why LLM Does Not Access PostGIS Directly:
1. **Security**: Direct SQL generation by LLMs allows SQL injection, unauthorized data exfiltration across tenant boundaries, and denial-of-service via expensive unindexed geospatial joins.
2. **Determinism**: PostGIS spatial operations require precise coordinate reference system transformations (SRID 4326 to SRID 3857/metric UTM). Parameterized tools ensure calculations are consistently performed using verified geodesy functions.
3. **Auditability**: Tool calls produce structured logs detailing which dataset, layer, and feature ID substantiated every claim made in the developer report.
4. **Map Synchronicity**: Tool calls return `MapAction` payloads that allow the React MapLibre frontend to automatically display markers, highlight roads, or fit bounds without parsing free-form text.

---

## 8. Map Action Contract

The AI response includes typed UI directives conforming to `MapAction`:
- `show_layer`: Turn on a specific layer in the WebGIS viewer.
- `hide_layer`: Turn off a specific layer.
- `highlight_feature`: Highlight specific geometry IDs on the map.
- `fit_bounds`: Zoom and pan to fit analyzed features.
- `show_marker`: Drop an analytical marker at a POI or coordinate.
- `clear_highlight`: Reset map highlight states.

---

## 9. Testing & Quality Assurance

- **48 Module 2A Unit & Contract Tests**: Passing (`tests/test_spatial_ai_tools.py`).
- **25 Module 1 Spatial Operation Tests**: Passing (`tests/test_spatial_knowledge.py`).
- **8 GIS Access Authorization Tests**: Passing (`tests/test_gis_access.py`).
- **Total Backend Suite**: 81 tests passing with zero regressions.
