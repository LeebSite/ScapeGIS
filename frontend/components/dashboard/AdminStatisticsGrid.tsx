"use client";

import { StatisticsCard } from "./StatisticsCard";
import { Users, UserCheck, CheckCircle, TrendingUp, Briefcase, Shield, Key } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle } from "lucide-react";
import type { UserStatisticsResponse } from "@/lib/api/AdminService";

interface AdminStatisticsGridProps {
    data: UserStatisticsResponse | undefined;
    isLoading: boolean;
    isError: boolean;
    refetch: () => void;
}

export function AdminStatisticsGrid({ data, isLoading, isError, refetch }: AdminStatisticsGridProps) {
    if (isLoading) {
        return (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {Array.from({ length: 7 }).map((_, i) => (
                    <Card key={i}>
                        <div className="p-6 space-y-2">
                            <Skeleton className="h-4 w-24" />
                            <Skeleton className="h-8 w-16" />
                            <Skeleton className="h-3 w-32" />
                        </div>
                    </Card>
                ))}
            </div>
        );
    }

    if (isError || !data) {
        return (
            <Card className="p-6">
                <div className="flex flex-col items-center justify-center space-y-4">
                    <AlertCircle className="h-12 w-12 text-destructive" />
                    <div className="text-center">
                        <h3 className="font-semibold text-lg">Failed to load statistics</h3>
                        <p className="text-sm text-muted-foreground mt-1">
                            There was an error loading the dashboard statistics
                        </p>
                    </div>
                    <Button onClick={refetch} variant="outline">
                        Retry
                    </Button>
                </div>
            </Card>
        );
    }

    // Calculate users by role breakdown
    const roleBreakdown = data.users_by_role
        ? Object.entries(data.users_by_role)
            .map(([role, count]) => `${role}: ${count}`)
            .join(", ")
        : "N/A";

    // Calculate users by auth provider breakdown
    const authBreakdown = data.users_by_auth_provider
        ? Object.entries(data.users_by_auth_provider)
            .map(([provider, count]) => `${provider}: ${count}`)
            .join(", ")
        : "N/A";

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <StatisticsCard
                title="Total Users"
                value={data.total_users}
                icon={Users}
                description="All registered users"
            />

            <StatisticsCard
                title="Active Users"
                value={data.active_users}
                icon={UserCheck}
                description={`${data.inactive_users ?? 0} inactive`}
            />

            <StatisticsCard
                title="Verified Users"
                value={data.verified_users}
                icon={CheckCircle}
                description={`${Math.round((data.verified_users / data.total_users) * 100)}% of total`}
            />

            <StatisticsCard
                title="New Users (30d)"
                value={data.new_users_last_30_days}
                icon={TrendingUp}
                description="Last 30 days"
            />

            <StatisticsCard
                title="Total Workspaces"
                value={data.total_workspaces ?? 0}
                icon={Briefcase}
                description="Active workspaces"
            />

            <StatisticsCard
                title="Users by Role"
                value={data.users_by_role ? Object.values(data.users_by_role).reduce((a, b) => a + b, 0) : 0}
                icon={Shield}
                subtitle={roleBreakdown}
            />

            <StatisticsCard
                title="Auth Providers"
                value={data.users_by_auth_provider ? Object.keys(data.users_by_auth_provider).length : 0}
                icon={Key}
                subtitle={authBreakdown}
            />
        </div>
    );
}
