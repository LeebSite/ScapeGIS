import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function NotificationsPanel() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Notifikasi</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2 text-sm">
          <li className="text-muted-foreground">Tidak ada notifikasi baru</li>
        </ul>
      </CardContent>
    </Card>
  );
}
