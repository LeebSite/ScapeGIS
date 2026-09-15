import http from "./http";
import type { AIPromptLog } from "../types";

export interface ChatRequest {
  message: string;
  history?: { role: "user" | "assistant"; content: string }[];
  workspace_id: string; // Added workspace_id
  project_id?: string;
}

export interface ChatResponse {
  message: string;
  data?: any; // For map data or analysis results
}

export interface SpatialAnalysisRequest {
  operation: "buffer" | "intersect" | "union" | "difference";
  parameters: any;
  workspace_id: string; // Added workspace_id
  project_id?: string;
}

export interface SpatialAnalysisResponse {
  result: any; // GeoJSON
}

export const aiAPI = {
  /**
   * Send a message to the AI assistant
   * POST /ai/chat
   */
  chat: (data: ChatRequest) => http.post<ChatResponse>("/ai/chat", data),

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
