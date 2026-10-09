import http from "./http";
import type { AIPromptLog } from "../types";

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

export interface SpatialFact {
  category: string;
  subcategory?: string;
  count?: number;
  min_distance_meters?: number;
  nearest_name?: string;
  details?: Record<string, any>;
}

export interface MapAction {
  action_type: string;
  target?: Record<string, any>;
  zoom_level?: number;
  highlight_layer?: string;
}

export interface SpatialAIResponse {
  success: boolean;
  answer: string;
  intent?: Record<string, any>;
  facts?: SpatialFact[];
  actions?: MapAction[];
  confidence?: number;
  model_version?: string;
  error?: string | null;
  metadata?: Record<string, any>;
}

// Aliases for backward compatibility with frontend consumers
export interface ChatRequest extends SpatialAIChatRequest {}

export interface ChatResponse extends SpatialAIResponse {
  message: string; // mapped from backend 'answer'
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
   * Automatically normalizes response so both `answer` and legacy `message` fields are populated.
   */
  chat: async (data: ChatRequest) => {
    const payload: SpatialAIChatRequest = {
      workspace_id: data.workspace_id,
      project_id: data.project_id || undefined,
      latitude: data.latitude ?? undefined,
      longitude: data.longitude ?? undefined,
      message: data.message,
      history: data.history || [],
    };
    const response = await http.post<SpatialAIResponse>("/spatial-ai/chat", payload);
    return {
      ...response,
      data: {
        ...response.data,
        message: response.data.answer,
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
