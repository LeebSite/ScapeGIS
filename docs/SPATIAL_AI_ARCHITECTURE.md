# ScapeGIS — Spatial AI Architecture & Reasoning Agent

## 1. Executive Summary

ScapeGIS Spatial AI bridges natural language reasoning with a verified PostGIS geospatial foundation for property developers.

### Core Principle: The Ground Truth Boundary
> **LLM is responsible for intent, reasoning, and synthesis.**  
> **Backend PostGIS services are strictly responsible for ground truth, geometric calculation, and authorization.**

Under no circumstances is an LLM allowed to execute arbitrary SQL, directly query database tables, or invent geometric measurements (distances, areas, coordinates).

---

## 2. Complete End-to-End Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                           Natural Language User Query                             |
|         "Saya ingin membangun kos. Bagaimana akses fasilitas kesehatan?"          |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                    POST /api/v1/spatial-ai/analyze (Module 2B API)                |
|   - Authenticated User (JWT Session)                                              |
|   - Multi-tenant Workspace Validation                                             |
|   - Project Containment Check                                                     |
|   - Coordinate Bounds Check (-90..90, -180..180)                                  |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                           SpatialAIContext Builder                                |
|   - Discovers authorized GIS datasets for workspace                               |
|   - Resolves active semantic layer concepts (hospital, road, boundary)            |
|   - Generates compact, AI-safe system instructions (<400 tokens)                  |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+===================================================================================+
|               BaseSpatialAIProvider Abstraction -> GeminiProvider                |
|                                                                                   |
|   1. Prime session with ScapeGIS System Prompt & Rules                            |
|   2. Pass 5 Controlled Tool Declarations from SpatialAIToolRegistry               |
|   3. Send user query with target coordinate anchor                                |
+===================================================================================+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        Google Gemini (gemini-3.8-flash)                           |
|   - Analyzes user intent                                                          |
|   - Emits structured FunctionCall (e.g. find_nearest, search_radius)              |
+-----------------------------------------------------------------------------------+
                                          |
                                FunctionCall
                                          |
                                          v
+===================================================================================+
|                   GeminiSpatialAgent (Orchestration Engine)                       |
|                                                                                   |
|   [Iteration Counter: max 8 calls (Loop Prevention)]                              |
|   - Validates requested tool against SpatialAIToolRegistry                        |
|   - Enforces backend tenant workspace_id & target coordinates                     |
|   - Dispatches execution to BaseSpatialTool                                       |
+===================================================================================+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        Verified PostGIS Backend Services                          |
|   - spatial_analysis_service (ST_Distance, ST_DWithin, ST_Contains, ST_Intersects)|
|   - spatial_context_service (Multi-domain neighborhood aggregator)                |
+-----------------------------------------------------------------------------------+
                                          |
                             Verified PostGIS Results
                                          |
                                          v
+===================================================================================+
|               Fact Extraction & FunctionResponse Serialization                    |
|   - Builds atomic SpatialFact objects (exact distance, count, containment)        |
|   - Attaches SpatialProvenance (dataset ID, layer ID, PostGIS op)                 |
|   - Formats FunctionResponse Part for Gemini (sanitizing heavy geometries)        |
+===================================================================================+
                                          |
                          send_tool_result(FunctionResponse)
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        Google Gemini (gemini-3.8-flash)                           |
|   - Synthesizes natural language answer strictly grounded in returned facts      |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                             Unified SpatialAIResponse                             |
|   - answer: Grounded natural language explanation                                |
|   - facts: List[SpatialFact] (exact metrics from PostGIS)                         |
|   - sources: List[SpatialProvenance] (audit trail)                                |
|   - map_actions: List[MapAction] (SHOW_MARKER, HIGHLIGHT_FEATURE)                 |
|   - tool_calls: List[Dict] (execution trace)                                      |
+-----------------------------------------------------------------------------------+
```

---

## 3. Provider Abstraction (`BaseSpatialAIProvider`)

To ensure vendor independence and maintainability, LLM operations are decoupled behind `BaseSpatialAIProvider`:

```python
class BaseSpatialAIProvider(ABC):
    @abstractmethod
    def start_conversation(self, system_instruction: str, tool_declarations: List[Dict[str, Any]]) -> Any: ...

    @abstractmethod
    def send_user_message(self, session: Any, message: str) -> ProviderStepResult: ...

    @abstractmethod
    def send_tool_result(self, session: Any, tool_name: str, result: Dict[str, Any]) -> ProviderStepResult: ...
```

### Concrete Implementation: `GeminiProvider`
- Integrates `google-generativeai` with the officially supported model `gemini-3.8-flash`.
- Automatically normalizes tool definitions to Gemini proto-compatible schemas (`type` to uppercase `STRING`, `NUMBER`, `INTEGER`, etc., and removes unsupported fields like `default`).
- Handles network exceptions, timeouts (`DeadlineExceeded`), and quota limits (`ResourceExhausted`), mapping them to `ProviderExecutionError`.

---

## 4. Tool Registry (`SpatialAIToolRegistry`)

The `SpatialAIToolRegistry` is the single source of truth for all spatial operations callable by the AI:

| Tool Name | PostGIS Operation | Input Schema | Output Schema | Purpose |
|---|---|---|---|---|
| `get_spatial_context` | Multi-domain aggregation | `GetSpatialContextInput` | `GetSpatialContextOutput` | Full spatial intelligence snapshot across all 5 domains (transport, health, worship, commercial, admin). |
| `find_nearest` | `ST_Distance` (`<->`) | `FindNearestInput` | `FindNearestOutput` | Locate nearest single POI (hospital, school, arterial road) with exact distance in meters and km. |
| `search_radius` | `ST_DWithin` | `SearchRadiusInput` | `SearchRadiusOutput` | Find all features within a specified radius (up to 50 km) sorted by distance. |
| `check_containment` | `ST_Contains` | `CheckContainmentInput` | `CheckContainmentOutput` | Determine which administrative boundary polygon (kecamatan/kelurahan) contains the coordinate. |
| `find_intersections` | `ST_Intersects` | `FindIntersectionsInput` | `FindIntersectionsOutput` | Identify roads or linear corridors intersecting a buffer zone around the coordinate. |

---

## 5. Multi-Tool Orchestration Loop & Safety

`GeminiSpatialAgent.analyze()` handles iterative tool calling:
1. **Loop Prevention**: Iterations are capped at `SPATIAL_AI_MAX_TOOL_CALLS` (default: 8).
2. **Tenant Parameter Injection**: Even if an LLM leaves out `workspace_id` or coordinates, the agent forcibly injects the authenticated request parameters, guaranteeing tenant isolation.
3. **Payload Sanitization**: Heavy PostGIS geometries (GeoJSON coordinates) are stripped before returning tool results to Gemini, keeping tokens compact and fast.
4. **MapAction Generation**: Every tool execution automatically generates typed UI commands (e.g. `SHOW_MARKER` at target location, `HIGHLIGHT_FEATURE` for nearest hospital).

---

## 6. Authorization Chain Enforcement

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

The LLM has zero authority over tenant boundary or authorization decisions.

---

## 7. Configuration Variables

| Variable | Default Value | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(Secret)* | Google Gemini API key. Never logged or exposed in API responses. |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Target Gemini model name confirmed by the current Google API. |
| `GEMINI_TIMEOUT_SECONDS` | `30` | Request timeout in seconds for LLM communication. |
| `SPATIAL_AI_MAX_TOOL_CALLS` | `8` | Maximum tool-call iterations per query to prevent runaway loops. |
| `SPATIAL_AI_MAX_HISTORY_MESSAGES` | `10` | Bounded sliding window for prior chat conversation history. |

---

## 8. Testing Strategy & Results

- **Automated Unit & Contract Tests**: Run deterministically via `MockAIProvider` without requiring external network access or live API credits.
- **Graceful Quota Handling**: Live smoke tests skip cleanly when Google API free tier quota is exhausted without failing the build.
- **Suite Metrics**:
  - Module 1 (Spatial Knowledge): 25/25 passed
  - GIS Access (Authorization): 8/8 passed
  - Module 2A (Tool Contracts): 48/48 passed
  - Module 2B (Gemini Reasoning Agent): 11/11 passed (1 live smoke test skipped on quota)
  - **Total Suite**: 92 passed, 1 skipped (100% green).


---

## 9. Module 2C — Spatial AI Chat API Specification

Module 2C establishes a secure, provider-agnostic conversational endpoint (`POST /api/v1/spatial-ai/chat`) extending the spatial reasoning engine for multi-turn conversational interaction.

### 9.1 Endpoint Definition

* **Path:** `POST /api/v1/spatial-ai/chat`
* **Authentication:** Mandatory Bearer JWT token (`Depends(get_current_user)`).
* **Tag:** `Spatial AI`

### 9.2 Request & Response Contracts

#### Request (`SpatialAIChatRequest`)
```json
{
  "workspace_id": "2a12cd6e-3644-4f72-989b-ac7737d06e3a",
  "project_id": null,
  "latitude": 0.507068,
  "longitude": 101.447779,
  "message": "Berapa jarak ke rumah sakit terdekat dari lokasi ini?",
  "history": [
    {
      "role": "user",
      "content": "Halo, saya sedang mengevaluasi lahan di Pekanbaru."
    },
    {
      "role": "assistant",
      "content": "Halo! Saya siap membantu analisis spasial berbasis PostGIS."
    }
  ]
}
```

* **Constraints:**
  * `workspace_id`: Required UUID, validated against user membership.
  * `project_id`: Optional UUID, verified to belong to the authorized workspace.
  * `latitude` & `longitude`: Optional coordinate anchor pair. If one is supplied, both must be supplied (`ge=-90, le=90` / `ge=-180, le=180`).
  * `message`: Required string, `min_length=1`, `max_length=2000`, non-whitespace.
  * `history`: List of `ChatMessage` objects, bounded to a maximum of 10 items.
  * `ChatMessage.role`: Strictly limited to `"user"` or `"assistant"`.
  * `ChatMessage.content`: String `min_length=1`, `max_length=2000`.

#### Response (`SpatialAIResponse`)
```json
{
  "answer": "Berdasarkan data GIS Kota Pekanbaru, fasilitas rumah sakit terdekat adalah Rumah Sakit Khusus dengan jarak 1.082 km.",
  "facts": [
    {
      "type": "distance",
      "category": "public_facility",
      "subcategory": "hospital",
      "statement": "Fasilitas hospital terdekat (Rumah Sakit Khusus) berjarak 1.082 km (1081.97 meter).",
      "value": 1081.97,
      "unit": "meter",
      "source_layer": "Dot_LOKASI_RumahSakit",
      "dataset_id": "adb542a8-4c47-413f-a98b-3592b7f7ef00"
    }
  ],
  "sources": [
    {
      "dataset_id": "adb542a8-4c47-413f-a98b-3592b7f7ef00",
      "dataset_name": "Kota Pekanbaru",
      "layer_id": "38d437b1-6134-4b00-a9c2-4fc9996d45e4",
      "layer_name": "Dot_LOKASI_RumahSakit",
      "semantic_category": "public_facility",
      "semantic_subcategory": "hospital",
      "operation": "ST_DistanceSphere",
      "feature_count_queried": 1
    }
  ],
  "map_actions": [
    {
      "type": "show_marker",
      "coordinates": { "latitude": 0.507068, "longitude": 101.447779 },
      "properties": { "title": "Lokasi Target Analisis" }
    },
    {
      "type": "highlight_feature",
      "layer_id": "38d437b1-6134-4b00-a9c2-4fc9996d45e4",
      "feature_ids": ["d65fdb66-85ee-4824-b56d-7bc2ca3a5e0c"],
      "properties": { "name": "Rumah Sakit Khusus", "distance_m": 1081.97 }
    }
  ],
  "tool_calls": [
    {
      "iteration": 1,
      "tool": "find_nearest",
      "arguments": { "subcategory": "hospital", "workspace_id": "..." },
      "success": true
    }
  ],
  "timestamp": "2026-10-10T02:50:00Z",
  "model": "gemini-3.8-flash"
}
```

### 9.3 Security & Boundary Enforcements

1. **Authentication Enforcement:** Unauthenticated requests return `401 Unauthorized`.
2. **Deterministic Workspace Boundary:** Workspace membership is verified in PostgreSQL against the authenticated `current_user.id`. The LLM cannot access cross-tenant data.
3. **GIS Entitlement Check:** Active dataset grants (`WorkspaceGISAccess.is_active == True`) are required before tools can execute. Empty grants return `403 Forbidden`.
4. **Prompt Injection Protection:** History turns mimicking system prompt headers (e.g. `[SYSTEM INSTRUCTION]`) are neutralized to `[PREVIOUS_CONTEXT]`.
5. **No SQL Execution:** The AI model cannot generate or execute raw SQL. All geometric queries route exclusively through `SpatialAIToolRegistry`.
6. **No Secret Leaks:** Provider credentials, database connection strings, and internal stack traces are suppressed from API responses (500 errors return sanitized message).

### 9.4 Error Semantics

| Status Code | Reason | Cause |
| :--- | :--- | :--- |
| `401 Unauthorized` | Not Authenticated | Missing, expired, or invalid JWT token. |
| `403 Forbidden` | Authorization Failure | User not in workspace, project not in workspace, or no active GIS entitlement. |
| `422 Unprocessable Entity` | Validation Error | Oversized message, >10 history items, invalid role, or unbalanced coordinate pair. |
| `400 Bad Request` | Spatial AI Error | Malformed provider candidates or semantic resolution errors. |
| `502 Bad Gateway` | Provider Execution Error | Gemini API timeout, quota exhaustion (429), or network error. |
| `503 Service Unavailable` | Configuration Error | `GEMINI_API_KEY` missing from backend configuration. |
| `500 Internal Server Error` | Unexpected Server Error | Uncaught internal exception; sanitized message returned without stack trace. |

### 9.5 Test Verification

Automated regression command:
```powershell
& "D:\ScapeGIS\backend\venv\Scripts\python.exe" -m pytest tests/test_spatial_ai_chat.py -v
```

Total regression suite: **109 passed, 1 skipped (0 failures)** across:
- `tests/test_spatial_ai_chat.py`: 17 passed
- `tests/test_gemini_spatial_agent.py`: 11 passed, 1 skipped
- `tests/test_spatial_ai_tools.py`: 48 passed
- `tests/test_spatial_knowledge.py`: 25 passed
- `tests/test_gis_access.py`: 8 passed
