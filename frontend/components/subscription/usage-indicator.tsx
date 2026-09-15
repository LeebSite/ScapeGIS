"use client";

import { useEffect, useState } from "react";
import { workspaceAPI } from "@/lib/api";
import type { WorkspaceUsageResponse } from "@/lib/api/WorkspaceService";
import { Progress } from "@/components/ui/progress"; // Assuming shadcn progress
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"; // Assuming shadcn alert
import { AlertTriangle } from "lucide-react";

interface UsageIndicatorProps {
    workspaceId: string;
}

export function UsageIndicator({ workspaceId }: UsageIndicatorProps) {
    const [usage, setUsage] = useState<WorkspaceUsageResponse | null>(null);

    useEffect(() => {
        const fetchUsage = async () => {
            try {
                const res = await workspaceAPI.getUsage(workspaceId);
                setUsage(res.data);
            } catch (error) {
                console.error("Failed to fetch usage:", error);
            }
        };
        if (workspaceId) fetchUsage();
    }, [workspaceId]);

    if (!usage) return null;

    // Calculate percentage for prompts
    // If limit is -1 (unlimited), show 0% used or handle visually
    const isUnlimitedPrompts = usage.prompts_limit === -1;
    const promptPercentage = isUnlimitedPrompts
        ? 0
        : Math.min(100, (usage.prompts_used_this_month / usage.prompts_limit) * 100);

    return (
        <div className="space-y-4 rounded-lg border p-4 bg-card text-card-foreground">
            <h3 className="font-semibold">Plan Usage</h3>

            <div className="space-y-2">
                <div className="flex justify-between text-sm">
                    <span>AI Prompts</span>
                    <span>
                        {usage.prompts_used_this_month} / {isUnlimitedPrompts ? "∞" : usage.prompts_limit}
                    </span>
                </div>
                {!isUnlimitedPrompts && <Progress value={promptPercentage} />}
            </div>

            <div className="space-y-2">
                <div className="flex justify-between text-sm">
                    <span>Projects</span>
                    <span>
                        {usage.projects_count} / {usage.projects_limit === -1 ? "∞" : usage.projects_limit}
                    </span>
                </div>
            </div>

            <div className="space-y-2">
                <div className="flex justify-between text-sm">
                    <span>Team Members</span>
                    <span>
                        {usage.members_count} / {usage.members_limit === -1 ? "∞" : usage.members_limit}
                    </span>
                </div>
            </div>

            {!isUnlimitedPrompts && promptPercentage >= 80 && (
                <Alert variant="destructive">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertTitle>Low Credits</AlertTitle>
                    <AlertDescription>
                        You're running low on AI prompts. Upgrade for more.
                    </AlertDescription>
                </Alert>
            )}
        </div>
    );
}
