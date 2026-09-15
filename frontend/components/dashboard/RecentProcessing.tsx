import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function RecentProcessing() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent GIS Processing</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">No recent processing activity</p>
      </CardContent>
    </Card>
  );
}
