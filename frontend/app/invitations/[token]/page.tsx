"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { CheckCircle2, XCircle, Clock, Loader2, Building2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { workspaceAPI } from "@/lib/api/WorkspaceService";
import { useAuthStore } from "@/lib/store";

type State = "idle" | "loading" | "success" | "expired" | "already_accepted" | "wrong_email" | "error";

interface ResultData {
    workspace_name?: string;
    workspace_id?: string;
    message?: string;
}

function InvitationErrorCard({
    icon,
    iconBg,
    title,
    description,
    action,
}: {
    icon: React.ReactNode;
    iconBg: string;
    title: string;
    description: string;
    action: { label: string; onClick: () => void };
}) {
    return (
        <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
            <Card className="w-full max-w-md text-center">
                <CardHeader>
                    <div className="flex justify-center mb-3">
                        <div className={`h-16 w-16 rounded-full ${iconBg} flex items-center justify-center`}>
                            {icon}
                        </div>
                    </div>
                    <CardTitle>{title}</CardTitle>
                    <CardDescription>{description}</CardDescription>
                </CardHeader>
                <CardContent>
                    <Button className="w-full" onClick={action.onClick}>
                        {action.label}
                    </Button>
                </CardContent>
            </Card>
        </div>
    );
}

export default function InvitationPage() {
    const { token } = useParams<{ token: string }>();
    const router = useRouter();
    const { user, isAuthenticated, isInitialized, initializeAuth } = useAuthStore();
    const [state, setState] = useState<State>("idle");
    const [result, setResult] = useState<ResultData>({});

    useEffect(() => {
        if (!isInitialized) initializeAuth();
    }, [isInitialized, initializeAuth]);

    useEffect(() => {
        if (!isInitialized) return;
        if (!isAuthenticated) {
            router.push(`/login?redirect=/invitations/${token}`);
            return;
        }
        if (state !== "idle") return;

        const accept = async () => {
            setState("loading");
            try {
                const res = await workspaceAPI.acceptInvitation(token);
                setResult({ workspace_name: res.data.workspace_name, workspace_id: res.data.workspace_id });
                setState("success");
            } catch (err: any) {
                const httpStatus = err?.response?.status;
                const detail: string = err?.response?.data?.detail || "";
                if (httpStatus === 410 || detail.toLowerCase().includes("expired")) {
                    setState("expired");
                } else if (httpStatus === 409) {
                    setState("already_accepted");
                } else if (httpStatus === 403) {
                    setState("wrong_email");
                    setResult({ message: detail });
                } else {
                    setState("error");
                    setResult({ message: detail || "Unexpected error" });
                }
            }
        };
        accept();
    }, [isInitialized, isAuthenticated, token, state]);

    if (state === "idle" || state === "loading") {
        return (
            <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
                <Card className="w-full max-w-md text-center">
                    <CardContent className="pt-10 pb-10 flex flex-col items-center gap-4">
                        <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                            <Loader2 className="h-8 w-8 text-primary animate-spin" />
                        </div>
                        <div>
                            <h2 className="text-xl font-semibold">Processing Invitation</h2>
                            <p className="text-muted-foreground text-sm mt-1">Please wait...</p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    if (state === "success") {
        return (
            <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
                <Card className="w-full max-w-md text-center">
                    <CardHeader>
                        <div className="flex justify-center mb-3">
                            <div className="h-16 w-16 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                                <CheckCircle2 className="h-8 w-8 text-green-600" />
                            </div>
                        </div>
                        <CardTitle>Welcome to the Team!</CardTitle>
                        <CardDescription>
                            You have successfully joined <strong>{result.workspace_name}</strong>.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground mb-6">
                            <Building2 className="h-4 w-4" />
                            <span>{result.workspace_name}</span>
                        </div>
                        <Button className="w-full" onClick={() => router.push("/dashboard/developer/workspaces")}>
                            Go to Workspace
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    const errorStates: Record<string, { icon: React.ReactNode; iconBg: string; title: string; description: string; action: { label: string; href: string } }> = {
        expired: {
            icon: <Clock className="h-8 w-8 text-orange-500" />,
            iconBg: "bg-orange-100 dark:bg-orange-900/30",
            title: "Invitation Expired",
            description: "This invitation has expired. Please ask the workspace owner to send a new one.",
            action: { label: "Go to Dashboard", href: "/dashboard/developer" },
        },
        already_accepted: {
            icon: <CheckCircle2 className="h-8 w-8 text-blue-500" />,
            iconBg: "bg-blue-100 dark:bg-blue-900/30",
            title: "Already a Member",
            description: "This invitation has already been accepted. You are already in this workspace.",
            action: { label: "View Workspaces", href: "/dashboard/developer/workspaces" },
        },
        wrong_email: {
            icon: <XCircle className="h-8 w-8 text-destructive" />,
            iconBg: "bg-destructive/10",
            title: "Wrong Account",
            description: result.message || "This invitation was sent to a different email address.",
            action: { label: "Go to Dashboard", href: "/dashboard/developer" },
        },
        error: {
            icon: <XCircle className="h-8 w-8 text-destructive" />,
            iconBg: "bg-destructive/10",
            title: "Something Went Wrong",
            description: result.message || "Could not process the invitation. Please try again.",
            action: { label: "Go to Dashboard", href: "/dashboard/developer" },
        },
    };

    const cfg = errorStates[state] || errorStates.error;
    return (
        <InvitationErrorCard
            icon={cfg.icon}
            iconBg={cfg.iconBg}
            title={cfg.title}
            description={cfg.description}
            action={{ label: cfg.action.label, onClick: () => router.push(cfg.action.href) }}
        />
    );
}