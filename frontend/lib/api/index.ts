/**
 * API Services Index
 * 
 * This file exports all API services for easy import throughout the application.
 * 
 * Usage:
 * import { authAPI, adminAPI, aiAPI, subscriptionAPI } from '@/lib/api';
 */

// Note: Auth functions are now exported directly from './authService'
// Use: import { login, getCurrentUser, etc } from '@/lib/api/authService'

export { adminAPI } from "./AdminService";
export { aiAPI } from "./AIService";
export { subscriptionAPI } from "./SubscriptionService";
export { workspaceAPI } from "./WorkspaceService";
export { invitationAPI } from "./InvitationService";
export { projectAPI } from "./ProjectService";
export { layerAPI } from "./LayerService";

// Re-export types

export type {
  UpdateUserStatusRequest,
  UpdateUserRoleRequest,
  UserDetail,
  MessageResponse,
} from "./AdminService";

export type {
  ChatRequest,
  ChatResponse,
  SpatialAnalysisRequest,
  SpatialAnalysisResponse,
} from "./AIService";

export type {
  SubscriptionRequestResult,
} from "./SubscriptionService";

