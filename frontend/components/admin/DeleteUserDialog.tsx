"use client";

import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AlertTriangle, Loader2 } from "lucide-react";
import { useState } from "react";

interface DeleteUserDialogProps {
    userId: string;
    userName: string;
    userEmail: string;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onConfirm: () => Promise<void>;
}

export function DeleteUserDialog({
    userId,
    userName,
    userEmail,
    open,
    onOpenChange,
    onConfirm,
}: DeleteUserDialogProps) {
    const [confirmEmail, setConfirmEmail] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const handleConfirm = async () => {
        if (confirmEmail !== userEmail) return;

        setIsLoading(true);
        try {
            await onConfirm();
            onOpenChange(false);
            setConfirmEmail("");
        } catch (error) {
            // Error handling is done in the parent component
        } finally {
            setIsLoading(false);
        }
    };

    const handleCancel = () => {
        setConfirmEmail("");
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent>
                <DialogHeader>
                    <div className="flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5 text-destructive" />
                        <DialogTitle>Delete User</DialogTitle>
                    </div>
                    <DialogDescription>
                        This action cannot be undone. This will permanently delete the user{" "}
                        <strong>{userName}</strong> and remove all their data from the system.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    <div className="space-y-2">
                        <Label htmlFor="confirm-email">
                            Type <strong>{userEmail}</strong> to confirm
                        </Label>
                        <Input
                            id="confirm-email"
                            value={confirmEmail}
                            onChange={(e) => setConfirmEmail(e.target.value)}
                            placeholder="Enter email to confirm"
                            disabled={isLoading}
                        />
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={handleCancel} disabled={isLoading}>
                        Cancel
                    </Button>
                    <Button
                        variant="destructive"
                        onClick={handleConfirm}
                        disabled={confirmEmail !== userEmail || isLoading}
                    >
                        {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Delete User
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
