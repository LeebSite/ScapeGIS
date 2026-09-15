// Re-export auth types for backward compatibility
import type { UserRole as AuthUserRole, User as AuthUser } from './types/auth';

export type UserRole = AuthUserRole;
export type User = AuthUser;


export interface Workspace {
  id: string;
  name: string;
  owner_id: string;
  subscription_id?: string;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceMember {
  id: string;
  workspace_id: string;
  user_id: string;
  role: "owner" | "admin" | "member";
  joined_at: string;
  user?: User;
}

export interface WorkspaceInvitation {
  id: string;
  workspace_id: string;
  email: string;
  invited_by: string; // User ID
  role: "admin" | "member";
  token: string;
  status: "pending" | "accepted" | "expired";
  expires_at: string;
  created_at: string;
}

export interface Subscription {
  id: string;
  name: "Free" | "Basic" | "Professional";
  max_prompts_per_month: number;
  max_projects: number;
  max_members: number;
  max_custom_maps: number;
  price_per_month: number;
  features: {
    custom_maps: boolean;
    advanced_ai: boolean;
  };
}

export interface Project {
  id: string;
  workspace_id: string; // Replaces organization_id
  created_by: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Layer {
  id: string;
  name: string;
  type: "vector" | "raster";
  region: string;
  subscription_level: "free" | "basic" | "professional";
  source?: string;
  created_at: string;
  updated_at: string;
}

export interface SubscriptionRequest {
  id: string;
  user_id: string;
  workspace_id: string;
  project_id?: string;
  region_requested: string;
  project_type: string;
  notes?: string;
  status: "pending" | "processing" | "approved" | "rejected";
  created_at: string;
  updated_at: string;
}

export interface AIPromptLog {
  id: string;
  user_id: string;
  workspace_id: string;
  project_id: string;
  prompt: string;
  response: string;
  created_at: string;
}

// API Error Response
export interface APIError {
  error: string;
  code?: string;
  details?: any;
}

// Map related types (kept from previous version if still relevant, otherwise can be refactored)
export interface MapLayer {
  id: string;
  name: string;
  type: string;
  visible: boolean;
  opacity?: number;
}

export interface GeoJSONFeature {
  type: "Feature";
  geometry: any;
  properties: any;
}

export interface MapData {
  type: "2d" | "3d";
  layers: string[];
  url?: string;
  features?: GeoJSONFeature[];
}


