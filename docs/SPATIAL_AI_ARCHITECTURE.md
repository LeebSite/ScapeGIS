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
