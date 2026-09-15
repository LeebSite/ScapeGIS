"use client";

import { useState } from "react";
import { subscriptionAPI } from "@/lib/api";
import type { Subscription, SubscriptionRequest } from "@/lib/types";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea"; // Assuming generic textarea or input
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAuthStore } from "@/lib/store";
import { useWorkspaceStore } from "@/lib/store";

interface UpgradeModalProps {
    plan: Subscription | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSuccess?: () => void;
}

export function UpgradeModal({ plan, open, onOpenChange, onSuccess }: UpgradeModalProps) {
    const [region, setRegion] = useState("");
    const [projectType, setProjectType] = useState("");
    const [notes, setNotes] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const { user } = useAuthStore();
    const { currentWorkspace } = useWorkspaceStore();

    const handleUpgrade = async () => {
        if (!plan || !user || !currentWorkspace) return;

        setIsLoading(true);
        try {
            const payload: any = {
                user_id: user.id,
                workspace_id: currentWorkspace.id,
                region_requested: region,
                project_type: projectType,
                notes: notes,
                // We need to send plan info too? The backend prompt implies request creates a SubscriptionRequest.
                // But the type definition for SubscriptionRequest doesn't explicitly store 'plan_id', but maybe it's implied by what user selects or handled by admin.
                // Wait, the prompt says: "User selects 'Basic' or 'Professional' -> Show form -> Submit request".
                // The SubscriptionRequest interface has `project_id`, `region_requested` etc.
                // It doesn't seem to have a field for "requested plan". Maybe user puts it in notes or it's inferred?
                // Let's add it to notes or assume the backend handles it based on context or a missing field in interface. 
                // Actually I'll append it to notes for now to be safe.
            };
            // NOTE: The prompt's SubscriptionRequest interface is missing a 'target_plan_id' or similar. 
            // I will assume the backend might need it, but strict to interface provided in prompt:
            /*
            interface SubscriptionRequest {
                workspace_id: string;
                region_requested: string;
                project_type: string;
                notes?: string;
            }
            */
            // So I will just use those fields.

            await subscriptionAPI.createRequest(payload);
            onSuccess?.();
            onOpenChange(false);
            setRegion("");
            setProjectType("");
            setNotes("");
        } catch (error) {
            console.error("Failed to submit request:", error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Upgrade to {plan?.name}</DialogTitle>
                    <DialogDescription>
                        Please provide details about your project needs.
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                        <Label htmlFor="region">Region Requested</Label>
                        <Input
                            id="region"
                            placeholder="e.g. Jakarta Pusat"
                            value={region}
                            onChange={(e) => setRegion(e.target.value)}
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="type">Project Type</Label>
                        <Select value={projectType} onValueChange={setProjectType}>
                            <SelectTrigger>
                                <SelectValue placeholder="Select type" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="perumahan">Perumahan</SelectItem>
                                <SelectItem value="komersial">Komersial</SelectItem>
                                <SelectItem value="mixed">Mixed Use</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="notes">Notes (Optional)</Label>
                        <Input
                            id="notes"
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            placeholder="Any specific requirements?"
                        />
                    </div>
                </div>
                <DialogFooter>
                    <Button onClick={handleUpgrade} disabled={isLoading || !region || !projectType}>
                        {isLoading ? "Submitting..." : "Submit Request"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
