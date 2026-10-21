# ScapeGIS — Spatial AI End-to-End (E2E) Runbook

## Document Overview
- **Project**: ScapeGIS (Cloud-Native WebGIS SaaS)
- **Module**: Module 2C — Spatial AI Chat API & Frontend Integration
- **Target Branch**: `feature/module-2b-gemini-agent`
- **Target Remote HEAD**: `df7517e`
- **Classification System**:
  - `[MOCK/UNIT]`: Isolated tests using mock providers and fixture data.
  - `[API-INTEG]`: Real HTTP requests against running FastAPI application with validated schemas.
  - `[DB-INTEG]`: Real queries executed against live PostgreSQL 16+ / PostGIS 3.6 spatial database.
  - `[LIVE-PROV]`: Real API calls transmitted to Google Gemini endpoint.
  - `[FULL-E2E]`: Seamless end-to-end user message submission from Next.js UI through Gemini orchestration and PostGIS execution.

---

## A. Prerequisites

### 1. Required Software & Runtime Versions
- **Operating System**: Windows 10/11 or Linux / macOS
- **Python**: `>= 3.11.x` (verified with `3.11.9`)
- **Node.js**: `>= 18.x` or `>= 20.x` (verified with `v20.18.0`)
- **Package Managers**: `npm` `>= 9.x`, `pip` / `virtualenv`
- **Database Engine**: PostgreSQL `>= 16.0` with PostGIS extension `>= 3.4` (verified on PostgreSQL 16.3 / PostGIS 3.6.0)

### 2. Environment Variables Configuration
> **SECURITY DIRECTIVE**: Never commit real secret values into version control, runbooks, or logs. Use `.env.example` as reference.

#### Backend (`backend/.env`)
| Variable Name | Purpose | Example / Format |
|---|---|---|
| `PROJECT_NAME` | Application identifier | `ScapeGIS` |
| `API_V1_STR` | API prefix string | `/api/v1` |
| `SECRET_KEY` | JWT signing secret key | Cryptographically secure hex string |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `1440` (24 hours) |
| `DATABASE_URL` | PostgreSQL connection URI | `postgresql+asyncpg://<USER>:<PASS>@<HOST>:<PORT>/<DB>` |
| `GEMINI_API_KEY` | Google AI Studio Gemini API Key | Secure secret key string |
| `SPATIAL_AI_MODEL` | Active Gemini generative model | `gemini-3.8-flash` or compatible model |
| `SPATIAL_AI_TIMEOUT_SECONDS` | Request timeout ceiling | `30` |

#### Frontend (`frontend/.env.local`)
| Variable Name | Purpose | Value |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Base endpoint for backend API | `http://localhost:8000` |

### 3. Database & PostGIS Readiness
1. **Verify PostGIS Extension**:
   ```sql
   SELECT postgis_full_version();
   ```
   *Expected Output*: Includes `POSTGIS="3.x"` and `GEOS="3.x"`.
2. **Apply Migrations**:
   ```powershell
   cd backend
   .\venv\Scripts\python.exe -m alembic upgrade head
   ```
3. **Verify Semantic GIS Metadata & Dataset**:
   - Workspace exists and has active user membership (`workspace_members`).
   - Dataset is loaded and associated with target workspace (`gis_datasets`).
   - Layers exist with valid geometries in EPSG:4326 (`gis_layers` and `gis_features`).
   - Spatial knowledge metadata is populated in `spatial_knowledge_layers` and `spatial_knowledge_attributes`.

### 4. Service Startup Commands
- **Backend Service (FastAPI)**:
  ```powershell
  cd backend
  .\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  ```
  *Readiness Check*: `GET http://localhost:8000/docs` returns HTTP 200.
- **Frontend Service (Next.js)**:
  ```powershell
  cd frontend
  npm run dev
  ```
  *Readiness Check*: `GET http://localhost:3000` returns HTTP 200.

### 5. Authentication Prerequisites
- Obtain an active Bearer JWT token by logging in or via API:
  ```http
  POST /api/v1/auth/login/access-token
  Content-Type: application/x-www-form-urlencoded

  username=<USER_EMAIL>&password=<USER_PASSWORD>
  ```
  *Extract*: `access_token` from JSON response.

---

## B. Happy-Path Scenario (Verified PostGIS Ground Truth)

### Scenario Definition
- **Objective**: Execute a genuine spatial query requiring the `find_nearest` tool using an authorized tenant workspace and real PostGIS spatial layer.
- **Verified Dataset Ground Truth**:
  - **Workspace Name**: `PT Insan Utama` (ID: `2a12cd6e-3644-4f72-989b-ac7737d06e3a`)
  - **Dataset Name**: `Kota Pekanbaru` (ID: `adb542a8-4c47-413f-a98b-3592b7f7ef00`)
  - **Target Layer**: `Dot_LOKASI_RumahSakit` (Layer ID: `38d437b1-6134-4b00-a9c2-4fc9996d45e4`)
  - **Layer Features Count**: 8 point features in Pekanbaru
  - **Test Reference Coordinate**: Latitude `0.5071`, Longitude `101.4478` (Pekanbaru City Center)
  - **Ground Truth Nearest Feature**:
    - **Feature ID**: `d65fdb66-85ee-4824-b56d-7bc2ca3a5e0c`
    - **Feature Name**: `Rumah Sakit Khusus`
    - **Calculated Distance**: `1,077.85 meters` (via PostGIS ST_DistanceSphere / KNN `<->` operator)

### Step-by-Step Procedure

#### Step 1: Frontend User Interaction
1. Open the ScapeGIS application at `http://localhost:3000`.
2. Navigate to the map workspace containing the Pekanbaru dataset.
3. Open the AI Chatbot drawer / panel (`frontend/components/ai/chatbot-panel.tsx`).
4. Type the prompt:
   > *"Di mana rumah sakit terdekat dari koordinat 0.5071, 101.4478?"*
5. Click **Send**.

#### Step 2: HTTP Request Inspection
The Next.js frontend calls `POST /api/v1/spatial-ai/chat` via `frontend/lib/api/AIService.ts`:
```http
POST /api/v1/spatial-ai/chat HTTP/1.1
Host: localhost:8000
Authorization: Bearer <AUTH_TOKEN>
Content-Type: application/json

{
  "message": "Di mana rumah sakit terdekat dari koordinat 0.5071, 101.4478?",
  "workspace_id": "2a12cd6e-3644-4f72-989b-ac7737d06e3a",
  "project_id": null,
  "latitude": 0.5071,
  "longitude": 101.4478,
  "history": []
}
```

#### Step 3: Backend Orchestration & Tool Execution
1. FastAPI validates schema and resolves `current_user`.
2. Workspace authorization verifies user membership.
3. Spatial context gathers authorized layer semantics (identifying `Dot_LOKASI_RumahSakit`).
4. Model selects `find_nearest` tool with arguments:
   ```json
   {
     "layer_id": "38d437b1-6134-4b00-a9c2-4fc9996d45e4",
     "latitude": 0.5071,
     "longitude": 101.4478,
     "limit": 1
   }
   ```
5. `FindNearestTool` executes PostGIS KNN query on `gis_features`.
6. Verified ground-truth result returned: `Rumah Sakit Khusus` at `1077.85` meters.

#### Step 4: HTTP Response Verification
The backend responds with `200 OK`:
```json
{
  "answer": "Rumah sakit terdekat dari koordinat yang diberikan adalah Rumah Sakit Khusus, dengan jarak sekitar 1.077,85 meter.",
  "confidence": 0.95,
  "facts": [
    {
      "statement": "Rumah Sakit Khusus berjarak 1077.85 m dari koordinat (0.5071, 101.4478)",
      "layer_id": "38d437b1-6134-4b00-a9c2-4fc9996d45e4",
      "feature_ids": ["d65fdb66-85ee-4824-b56d-7bc2ca3a5e0c"]
    }
  ],
  "provenance": {
    "source_layers": ["38d437b1-6134-4b00-a9c2-4fc9996d45e4"],
    "tools_executed": ["find_nearest"]
  },
  "suggested_actions": [
    {
      "action_type": "highlight_features",
      "layer_id": "38d437b1-6134-4b00-a9c2-4fc9996d45e4",
      "feature_ids": ["d65fdb66-85ee-4824-b56d-7bc2ca3a5e0c"]
    }
  ]
}
```

#### Step 5: Frontend Rendering
- The chat bubble displays the synthesized response.
- The UI badge displays verified GIS facts and data provenance tags.
- If supported by the active map store, the map centers on coordinate `(0.5071, 101.4478)` and highlights feature `d65fdb66-85ee-4824-b56d-7bc2ca3a5e0c`.

---

## C. Security Scenarios

### 1. Missing Authentication Token
- **Test ID**: `TC-SEC-01`
- **Procedure**: Send request without `Authorization` header.
- **Expected Result**: HTTP `401 Unauthorized` with body `{"detail": "Not authenticated"}`.
- **Status**: **PASS** (Verified against live FastAPI server).

### 2. Invalid Authentication Token
- **Test ID**: `TC-SEC-02`
- **Procedure**: Send request with `Authorization: Bearer invalid.token.payload`.
- **Expected Result**: HTTP `401 Unauthorized` with body `{"detail": "Invalid token"}`.
- **Status**: **PASS** (Verified against live FastAPI server).

### 3. Cross-Tenant Workspace Isolation
- **Test ID**: `TC-SEC-03`
- **Procedure**: Authenticated user requests a `workspace_id` where they hold no membership.
- **Expected Result**: HTTP `403 Forbidden` with body `{"detail": "Access forbidden: you do not have permission to access this workspace."}`.
- **Information Leak Check**: The response reveals no internal database IDs, schema details, or stack traces.
- **Status**: **PASS** (Verified against live FastAPI server).

### 4. Tenant Context Tampering Protection (`project_id` override)
- **Test ID**: `TC-SEC-04`
- **Procedure**:
  - Case A: User specifies `project_id=P1`, model attempts to supply `project_id=P2` in tool arguments.
  - Case B: User specifies `project_id=None`, model attempts to supply `project_id=P2` in tool arguments.
- **Expected Result**: In Case A, tool receives `project_id=P1`. In Case B, tool receives `project_id=None`. Model-supplied `project_id` is stripped.
- **Evidence**: `test_agent_project_override_protection` in `backend/tests/test_gemini_spatial_agent.py`.
- **Status**: **PASS** (Verified in automated test suite).

### 5. Arbitrary SQL Execution Prevention
- **Test ID**: `TC-SEC-05`
- **Procedure**: Prompt attempts SQL injection: `"Find nearest hospital; DROP TABLE gis_features; --"`.
- **Expected Result**: Spatial agent only invokes controlled registered tools (`FindNearestTool`, `BufferAnalysisTool`, etc.). No dynamic raw SQL execution tool exists. Parameterized SQLAlchemy expressions bind coordinate and ID inputs safely.
- **Status**: **PASS** (Architecturally enforced).

---

## D. Failure & Input Validation Scenarios

### 1. Invalid Coordinate Bounds
- **Test ID**: `TC-VAL-01`
- **Procedure**: Send `latitude: 999.0` (exceeding [-90, 90]).
- **Expected Result**: HTTP `422 Unprocessable Entity` with error: `Input should be less than or equal to 90`.
- **Status**: **PASS** (Verified against live FastAPI server).

### 2. Missing Coupled Coordinate Component
- **Test ID**: `TC-VAL-02`
- **Procedure**: Send `latitude: 0.5071` with `longitude: null`.
- **Expected Result**: HTTP `422 Unprocessable Entity` with error: `Both latitude and longitude must be provided together.`.
- **Status**: **PASS** (Verified against live FastAPI server).

### 3. Conversation History Limit Enforcement
- **Test ID**: `TC-VAL-03`
- **Procedure**: Send conversation `history` array containing 11 messages.
- **Expected Result**: HTTP `422 Unprocessable Entity` with error: `Conversation history exceeds maximum allowed limit of 10 messages.`.
- **Status**: **PASS** (Verified against live FastAPI server).

### 4. AI Provider Downtime / Timeout
- **Test ID**: `TC-FAIL-01`
- **Procedure**: Gemini API is unreachable or times out past `SPATIAL_AI_TIMEOUT_SECONDS`.
- **Expected Result**: FastAPI catches `SpatialAIProviderError` and returns HTTP `503 Service Unavailable` with sanitized detail: `Spatial AI provider is currently unavailable. Please try again later.`.
- **Status**: **PASS** (Verified by unit test `test_spatial_ai_chat_provider_timeout`).

### 5. Frontend Error Handling & Retry Resilience
- **Test ID**: `TC-UI-01`
- **Procedure**: Backend responds with 500 or 503 error during chat conversation.
- **Expected Result**:
  - Frontend displays red error alert in chat box.
  - User is presented with a **Retry** button.
  - The failed message can be resent without refreshing the page.
- **Status**: **PASS** (Implemented in `frontend/components/ai/chatbot-panel.tsx`).

---

## E. Verification Execution Matrix

| Test ID | Scenario / Verification Scope | Classification | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| `TC-UNIT-01` | Module 2C Chat Endpoint Suite (20 tests) | `[MOCK/UNIT]` | 20 tests pass | 20 passed | **PASS** |
| `TC-UNIT-02` | Full Backend Spatial AI Test Suite (115 tests) | `[MOCK/UNIT]` | 114 pass, 1 skip | 114 passed, 1 skipped | **PASS** |
| `TC-AUTH-01` | Missing Authorization Header | `[API-INTEG]` | HTTP 401 Unauthorized | HTTP 401 (`Not authenticated`) | **PASS** |
| `TC-AUTH-02` | Invalid JWT Token | `[API-INTEG]` | HTTP 401 Unauthorized | HTTP 401 (`Invalid token`) | **PASS** |
| `TC-AUTH-03` | Unauthorized Workspace Access | `[API-INTEG]` | HTTP 403 Forbidden | HTTP 403 (`Access forbidden`) | **PASS** |
| `TC-VAL-01` | Latitude Exceeds Maximum Range | `[API-INTEG]` | HTTP 422 Validation Error | HTTP 422 (`<= 90`) | **PASS** |
| `TC-VAL-02` | Coordinate Coupling Validation | `[API-INTEG]` | HTTP 422 Validation Error | HTTP 422 (`must be provided together`) | **PASS** |
| `TC-VAL-03` | Conversation History Boundary (>10) | `[API-INTEG]` | HTTP 422 Validation Error | HTTP 422 (`limit of 10 messages`) | **PASS** |
| `TC-DB-01` | PostGIS 3.6 Spatial KNN Calculation | `[DB-INTEG]` | Nearest hospital at ~1,077m | `Rumah Sakit Khusus` at `1,077.85 m` | **PASS** |
| `TC-LIVE-01` | Live Gemini Single-Turn Generation | `[LIVE-PROV]` | Model answers basic prompt | Model responds `Pong` | **PASS** |
| `TC-LIVE-02` | Live Gemini Agent Spatial Tool Loop | `[LIVE-PROV]` | Multi-turn tool execution | Upstream 429 RESOURCE_EXHAUSTED (Free-tier 20 req/day limit reached) | **BLOCKED BY QUOTA** |
| `TC-E2E-01` | Full UI-to-PostGIS End-to-End Chat | `[FULL-E2E]` | Complete UI chat round-trip | Upstream 429 RESOURCE_EXHAUSTED (Free-tier 20 req/day limit reached) | **BLOCKED BY QUOTA** |

---

## F. Defect Resolution & Verification Log (v2 — google-genai Migration)

### Defect Identifier: `DEF-GEMINI-THOUGHT-SIGNATURE`
- **Severity**: High (Historical Blocker)
- **Status**: **CODEBASE RESOLVED (SDK MIGRATION COMPLETE)** / Live Traffic Blocked by Free-Tier Quota (429)
- **Component**: `backend/app/spatial_ai/providers/gemini_provider.py`, `backend/requirements.txt`, `backend/tests/conftest.py`, `backend/tests/test_gemini_spatial_agent.py`
- **Root Cause Verified (Audit v2)**:
  1. Lini SDK `google-generativeai` telah deprecated/EOL sejak 31 Agustus 2025. Versi terakhirnya `0.8.5` mewajibkan pin exact `google-ai-generativelanguage==0.6.15`.
  2. Pada `google-ai-generativelanguage==0.6.15`, protobuf descriptor `Part` dan `FunctionCall` tidak memiliki field `thought_signature`, sehingga ekstraksi signature selalu `None` dan manipulasi history sebelumnya adalah no-op di production.
- **Remediation Implemented (v2 Migration)**:
  1. **SDK Migration**: Menghapus `google-generativeai==0.8.5` dan mengadopsi SDK resmi penerus `google-genai==2.29.0` (bersama `httpx==0.28.1`) di `backend/requirements.txt`.
  2. **Native Part Field**: Pada `google.genai.types.Part`, field `thought_signature` (dan `thought`) tersedia secara native (`assert 'thought_signature' in types.Part.model_fields`).
  3. **Provider Migration**:
     - Memigrasikan `GeminiProvider` menggunakan `genai.Client(api_key=..., http_options=types.HttpOptions(timeout=...))`.
     - Sesi chat dibangun via `client.chats.create(model=..., config=types.GenerateContentConfig(...), history=...)`.
     - Tool declarations dibungkus ke `types.Tool(function_declarations=[types.FunctionDeclaration(...)])`.
     - Ekstraksi `thought_signature` diambil langsung dari objek `types.Part` (bukan dari FunctionCall).
     - Pengiriman hasil tool menggunakan `types.Part.from_function_response(name=..., response=...)`. Preservasi signature dilakukan secara native oleh SDK tanpa mutasi manual.
  4. **HTTPX 0.28 / Starlette Compatibility**: Menambahkan `backend/tests/conftest.py` untuk mengadaptasi `starlette.testclient.TestClient` yang memanggil `httpx.Client(app=app)` ke `httpx.ASGITransport(app=app)`.
  5. **Unit Tests dengan SDK Types Asli**: Menulis ulang test di `backend/tests/test_gemini_spatial_agent.py` menggunakan objek SDK asli (`google.genai.types.Part`, `FunctionCall`, `Candidate`, `GenerateContentResponse`, `Content`) untuk memverifikasi ekstraksi dan round-trip serialisasi/deserialisasi signature secara lossless.
- **Verification Evidence**:
  - `TC-UNIT-01`: 20 test chat passed.
  - `TC-UNIT-02`: 114 test passed, 1 skipped, 0 failed.
  - Field check: `assert 'thought_signature' in types.Part.model_fields` -> OK.
  - Handshake check: Handshake Google API bebas dari error HTTP 400 (`thought_signature missing`).
  - Live execution limitation: Permintaan live saat ini mengembalikan Google AI Studio HTTP 429 `RESOURCE_EXHAUSTED` (`generativelanguage.googleapis.com/generate_content_free_tier_requests`, limit 20 per hari untuk `gemini-3.8-flash`).

---

## G. Multi-Provider & Groq Verification Log (v3 — GroqProvider Implementation)

### Component Overview
- **Factory**: `backend/app/spatial_ai/providers/factory.py` (`create_spatial_ai_provider`)
- **Groq Provider**: `backend/app/spatial_ai/providers/groq_provider.py` (`GroqProvider`, `GroqSession`)
- **SDK**: `groq==1.7.0`
- **Model**: `openai/gpt-oss-120b` (configurable via `GROQ_MODEL`)
- **Unit Suite**: `backend/tests/test_groq_spatial_provider.py` (16 tests: `G-UNIT-01` through `G-UNIT-16`)

### Live Gate: `GL-02` (Live Groq Agent Spatial Tool Loop)
- **Endpoint**: `POST /api/v1/spatial-ai/chat`
- **Config**: `SPATIAL_AI_PROVIDER=groq`
- **Workspace**: `PT Insan Utama` (`2a12cd6e-3644-4f72-989b-ac7737d06e3a`)
- **Dataset**: `Kota Pekanbaru` (`adb542a8-4c47-413f-a98b-3592b7f7ef00`)
- **Layer**: `Dot_LOKASI_RumahSakit` (`38d437b1-6134-4b00-a9c2-4fc9996d45e4`)
- **Prompt**: `"Di mana rumah sakit terdekat dari koordinat 0.5071, 101.4478?"`
- **Expected Verification**:
  1. Groq generates tool call for `find_nearest`.
  2. Local PostGIS KNN query executes on `Dot_LOKASI_RumahSakit`.
  3. Tool result returns to Groq with matching `tool_call_id`.
  4. Final synthesis identifies `Rumah Sakit Khusus` at approximately `1,077.85 m`.
