import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function PendingMapRequests() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Pending Map Requests</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">No pending requests</p>
      </CardContent>
    </Card>
  );
}
