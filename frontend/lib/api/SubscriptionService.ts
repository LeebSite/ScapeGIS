import http from "./http";
import type { Subscription, SubscriptionRequest } from "../types";
import { API_CONFIG } from "./config";
import * as mockSubscription from "@/lib/mocks/subscriptions";

export interface SubscriptionRequestResult {
  id: string;
  status: "pending" | "processing" | "approved" | "rejected";
  created_at: string;
}

export const subscriptionAPI = {
  /**
   * Get all available subscription plans
   * GET /subscriptions/plans
   */
  getPlans: () => http.get<Subscription[]>("/subscriptions/plans"),

  /**
   * Create a subscription request (Upgrade)
   * POST /subscription-requests
   */
  createRequest: (data: Partial<SubscriptionRequest>) =>
    http.post<SubscriptionRequestResult>("/subscription-requests", data),

  /**
   * Get my subscription requests
   * GET /subscription-requests/me
   */
  getMyRequests: () =>
    http.get<SubscriptionRequestResult[]>("/subscription-requests/me"),

  /**
   * Get current subscription
   * GET /subscriptions/me
   */
  getCurrentSubscription: () =>
    http.get<Subscription>("/subscriptions/me"),
};
