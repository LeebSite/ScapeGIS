"use client";

import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Subscription } from "@/lib/types";

interface PlanCardProps {
    plan: Subscription;
    current?: boolean;
    onSelect?: (plan: Subscription) => void;
}

export function PlanCard({ plan, current, onSelect }: PlanCardProps) {
    return (
        <Card className={`flex flex-col ${current ? "border-primary shadow-lg" : ""}`}>
            <CardHeader>
                <div className="flex justify-between items-start">
                    <CardTitle>{plan.name}</CardTitle>
                    {current && <Badge variant="default">Current Plan</Badge>}
                </div>
                <CardDescription>
                    {plan.price_per_month === 0
                        ? "Free forever"
                        : `IDR ${plan.price_per_month.toLocaleString("id-ID")}/month`}
                </CardDescription>
            </CardHeader>
            <CardContent className="flex-1">
                <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-green-500" />
                        <span>{plan.max_prompts_per_month === -1 ? "Unlimited" : plan.max_prompts_per_month} AI Prompts</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-green-500" />
                        <span>{plan.max_projects === -1 ? "Unlimited" : plan.max_projects} Projects</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-green-500" />
                        <span>{plan.max_members === -1 ? "Unlimited" : plan.max_members} Team Members</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-green-500" />
                        <span>{plan.max_custom_maps === -1 ? "Unlimited" : plan.max_custom_maps} Custom Maps</span>
                    </div>
                    {plan.features.custom_maps && (
                        <div className="flex items-center gap-2 text-sm">
                            <Check className="h-4 w-4 text-green-500" />
                            <span>Custom Map Uploads</span>
                        </div>
                    )}
                    {plan.features.advanced_ai && (
                        <div className="flex items-center gap-2 text-sm">
                            <Check className="h-4 w-4 text-green-500" />
                            <span>Advanced AI Analysis</span>
                        </div>
                    )}
                </div>
            </CardContent>
            <CardFooter>
                <Button
                    className="w-full"
                    variant={current ? "outline" : "default"}
                    disabled={current}
                    onClick={() => onSelect?.(plan)}
                >
                    {current ? "Current Plan" : "Upgrade"}
                </Button>
            </CardFooter>
        </Card>
    );
}
