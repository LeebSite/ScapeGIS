"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { invitationAPI } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/lib/store";

export default function AcceptInvitationPage({ params }: { params: { token: string } }) {
    const router = useRouter();
    const { user, isAuthenticated } = useAuthStore();
    const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
    const [errorMessage, setErrorMessage] = useState("");

    const handleAccept = async () => {
        try {
            await invitationAPI.acceptInvitation(params.token);
            setStatus("success");
            setTimeout(() => {
                router.push("/dashboard");
            }, 2000);
        } catch (error: any) {
            console.error("Failed to accept invitation:", error);
            setStatus("error");
            setErrorMessage(error.response?.data?.message || "Failed to accept invitation");
        }
    };

    useEffect(() => {
        if (!isAuthenticated) {
            // Store return URL and redirect to login/register
            // For now, simpler approach: just show login button if not authenticated
            setStatus("error");
            setErrorMessage("Please login to accept the invitation");
        } else {
            // Auto accept or show confirmation?
            // Let's show confirmation
            setStatus("loading");
        }
    }, [isAuthenticated]);

    if (status === "loading" && isAuthenticated) {
        return (
            <div className="flex min-h-screen items-center justify-center p-4">
                <Card className="w-full max-w-md">
                    <CardHeader>
                        <CardTitle>Accept Invitation</CardTitle>
                        <CardDescription>You have been invited to join a workspace.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Button onClick={handleAccept} className="w-full">Accept Invitation</Button>
                    </CardContent>
                </Card>
            </div>
        )
    }

    if (status === "success") {
        return (
            <div className="flex min-h-screen items-center justify-center p-4">
                <Card className="w-full max-w-md">
                    <CardHeader>
                        <CardTitle className="text-green-600">Invitation Accepted!</CardTitle>
                        <CardDescription>Redirecting you to the dashboard...</CardDescription>
                    </CardHeader>
                </Card>
            </div>
        );
    }

    return (
        <div className="flex min-h-screen items-center justify-center p-4">
            <Card className="w-full max-w-md">
                <CardHeader>
                    <CardTitle className="text-red-600">Unable to Accept Invitation</CardTitle>
                    <CardDescription>{errorMessage}</CardDescription>
                </CardHeader>
                <CardContent>
                    {!isAuthenticated ? (
                        <div className="space-y-4">
                            <p>You need to be logged in to accept this invitation.</p>
                            <div className="flex gap-4">
                                <Button onClick={() => router.push(`/login?returnUrl=/invitations/${params.token}`)} variant="outline" className="w-full">Login</Button>
                                <Button onClick={() => router.push(`/register?returnUrl=/invitations/${params.token}`)} className="w-full">Register</Button>
                            </div>
                        </div>
                    ) : (
                        <Button onClick={() => router.push("/dashboard")} variant="outline" className="w-full">Go to Dashboard</Button>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
