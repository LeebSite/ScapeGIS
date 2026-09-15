import { Badge } from "@/components/ui/badge";

interface RoleBadgeProps {
    role: "admin" | "developer";
}

export function RoleBadge({ role }: RoleBadgeProps) {
    const variants = {
        admin: "destructive" as const,
        developer: "default" as const,
    };

    return (
        <Badge variant={variants[role]} className="capitalize">
            {role}
        </Badge>
    );
}
