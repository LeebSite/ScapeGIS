import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function AdminStats() {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Card>
        <CardHeader>
          <CardTitle>Total Users</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">1,234</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Active Maps</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">456</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>System Load</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">Normal</div>
        </CardContent>
      </Card>
    </div>
  );
}
