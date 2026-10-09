import http from "./http";
import type { AIPromptLog } from "../types";

/**
 * Maximum conversation history messages accepted by backend Spatial AI chat.
 * Aligns with backend settings.SPATIAL_AI_MAX_HISTORY_MESSAGES (default: 10).
 * Can be overridden via NEXT_PUBLIC_SPATIAL_AI_MAX_HISTORY if specified in frontend environment.
 */
export const SPATIAL_AI_MAX_HISTORY_MESSAGES = Number(
  process.env.NEXT_PUBLIC_SPATIAL_AI_MAX_HISTORY || 10
);

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface SpatialAIChatRequest {
  workspace_id: string;
  project_id?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  message: string;
  history?: ChatMessage[];
}

export interface SpatialProvenance {
  dataset_id: string;
  dataset_name?: string | null;
  layer_id: string;
  layer_name: string;
  semantic_category: string;
  semantic_subcategory: string;
  operation: string;
  feature_count_queried?: number | null;
}

export interface SpatialFact {
  type: string;
  category: string;
  subcategory: string;
  statement: string;
  value: any;
  unit?: string | null;
  source_layer?: string | null;
  dataset_id?: string | null;
}

export interface MapAction {
  type: string;
  layer_id?: string | null;
  feature_ids?: string[];
  coordinates?: Record<string, number> | null;
  bounds?: Record<string, number> | null;
  properties?: Record<string, any>;
}

export interface SpatialAIResponse {
  answer: string;
  facts: SpatialFact[];
  sources: SpatialProvenance[];
  map_actions: MapAction[];
  tool_calls: Record<string, any>[];
  timestamp: string;
  model?: string | null;
}

// Aliases for backward compatibility with frontend consumers
export interface ChatRequest extends SpatialAIChatRequest {}

export interface ChatResponse extends SpatialAIResponse {
  message: string; // compatibility alias mapped from answer
  actions?: MapAction[]; // compatibility alias mapped from map_actions
}

export interface SpatialAnalysisRequest {
  operation: "buffer" | "intersect" | "union" | "difference";
  parameters: any;
  workspace_id: string;
  project_id?: string;
}

export interface SpatialAnalysisResponse {
  result: any; // GeoJSON
}

export const aiAPI = {
  /**
   * Send a multi-turn message to the Spatial AI assistant
   * Calls POST /spatial-ai/chat (relative to http.ts baseURL which points to /api/v1)
   * Enforces SPATIAL_AI_MAX_HISTORY_MESSAGES defensively.
   * Automatically normalizes response so both `answer` and legacy `message` fields are populated.
   */
  chat: async (data: ChatRequest) => {
    const payload: SpatialAIChatRequest = {
      workspace_id: data.workspace_id,
      project_id: data.project_id || undefined,
      latitude: data.latitude ?? undefined,
      longitude: data.longitude ?? undefined,
      message: data.message,
      history: (data.history || []).slice(-SPATIAL_AI_MAX_HISTORY_MESSAGES),
    };
    const response = await http.post<SpatialAIResponse>("/spatial-ai/chat", payload);
    return {
      ...response,
      data: {
        ...response.data,
        message: response.data.answer,
        actions: response.data.map_actions,
      },
    };
  },

  /**
   * Perform spatial analysis
   * POST /ai/analysis
   */
  analyze: (data: SpatialAnalysisRequest) =>
    http.post<SpatialAnalysisResponse>("/ai/analysis", data),

  /**
   * Get prompt usage history
   * GET /ai/usage
   */
  getUsage: (workspaceId: string) =>
    http.get<AIPromptLog[]>(`/ai/usage?workspace_id=${workspaceId}`),
};
