"use client";

import { Switch } from "@/components/ui/switch";
import { useState } from "react";
import { Loader2 } from "lucide-react";

interface StatusToggleProps {
    userId: string;
    isActive: boolean;
    onToggle: (userId: string, isActive: boolean) => Promise<void>;
    disabled?: boolean;
}

export function StatusToggle({ userId, isActive, onToggle, disabled }: StatusToggleProps) {
    const [isLoading, setIsLoading] = useState(false);
    const [localActive, setLocalActive] = useState(isActive);

    const handleToggle = async (checked: boolean) => {
        setIsLoading(true);
        setLocalActive(checked); // Optimistic update

        try {
            await onToggle(userId, checked);
        } catch (error) {
            // Revert on error
            setLocalActive(!checked);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex items-center gap-2">
            {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            ) : (
                <Switch
                    checked={localActive}
                    onCheckedChange={handleToggle}
                    disabled={disabled || isLoading}
                />
            )}
            <span className="text-sm text-muted-foreground">
                {localActive ? "Active" : "Inactive"}
            </span>
        </div>
    );
}
