"use client";

import { useEffect, useState } from "react";
import { subscriptionAPI, workspaceAPI } from "@/lib/api";
import type { Subscription } from "@/lib/types";
import { PlanCard } from "@/components/subscription/plan-card";
import { UpgradeModal } from "@/components/subscription/upgrade-modal";
import { UsageIndicator } from "@/components/subscription/usage-indicator";
import { useWorkspaceStore } from "@/lib/store";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function SubscriptionPage() {
  const [plans, setPlans] = useState<Subscription[]>([]);
  const [currentPlan, setCurrentPlan] = useState<Subscription | null>(null);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<Subscription | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { currentWorkspace } = useWorkspaceStore();

  const fetchData = async () => {
    try {
      if (!currentWorkspace?.id) return;

      const [plansRes, subRes] = await Promise.all([
        subscriptionAPI.getPlans(),
        subscriptionAPI.getCurrentSubscription(),
      ]);
      setPlans(plansRes.data);
      setCurrentPlan(subRes.data);
    } catch (error) {
      console.error("Failed to fetch subscription data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (currentWorkspace?.id) {
      fetchData();
    }
  }, [currentWorkspace?.id]);

  const handleUpgradeClick = (plan: Subscription) => {
    setSelectedPlan(plan);
    setShowUpgradeModal(true);
  };

  if (!currentWorkspace) {
    return <div className="p-8">Please select a workspace first.</div>;
  }

  if (isLoading) {
    return <div className="p-8">Loading subscription data...</div>;
  }

  return (
    <div className="space-y-8 p-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Subscription & Billing</h2>
        <p className="text-muted-foreground">
          Manage your workspace subscription and usage.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <div className="col-span-4">
          <Card>
            <CardHeader>
              <CardTitle>Current Plan Usage</CardTitle>
              <CardDescription>Workspace: {currentWorkspace.name}</CardDescription>
            </CardHeader>
            <CardContent>
              <UsageIndicator workspaceId={currentWorkspace.id} />
            </CardContent>
          </Card>
        </div>
        <div className="col-span-3">
          <Card>
            <CardHeader>
              <CardTitle>Current Subscription</CardTitle>
            </CardHeader>
            <CardContent>
              {currentPlan ? (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">Plan</span>
                    <Badge>{currentPlan.name}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="font-medium">Price</span>
                    <span>IDR {currentPlan.price_per_month.toLocaleString("id-ID")}/mo</span>
                  </div>
                  {/* Add more details like renewal date if available */}
                </div>
              ) : (
                <p>No active subscription.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <div>
        <h3 className="text-xl font-semibold mb-4">Available Plans</h3>
        <div className="grid gap-6 md:grid-cols-3">
          {plans.map((plan) => (
            <PlanCard
              key={plan.id}
              plan={plan}
              current={currentPlan?.id === plan.id}
              onSelect={handleUpgradeClick}
            />
          ))}
        </div>
      </div>

      <UpgradeModal
        plan={selectedPlan}
        open={showUpgradeModal}
        onOpenChange={setShowUpgradeModal}
        onSuccess={() => {
          alert("Upgrade request submitted successfully!");
          // Optionally refresh requests list
        }}
      />
    </div>
  );
}
