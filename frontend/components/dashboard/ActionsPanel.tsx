import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

export function ActionsPanel() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Aksi Cepat</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-2">
          <Link href="/maps/pekanbaru" className="p-3 bg-primary text-primary-foreground rounded-md text-center">Permintaan Peta Baru (Demo)</Link>
          <Link href="/dashboard/developer/subscription" className="p-3 border rounded-md text-center">Kelola Langganan</Link>
        </div>
      </CardContent>
    </Card>
  );
}
