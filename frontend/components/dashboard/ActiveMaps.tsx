import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { listMaps } from "@/lib/maps";

export function ActiveMaps() {
  const maps = listMaps();

  return (
    <div>
      <h3 className="text-lg font-semibold mb-2">Peta Aktif</h3>
      <div className="grid gap-3 md:grid-cols-3">
        {maps.map((m) => (
          <Card key={m.id}>
            <CardHeader>
              <CardTitle>{m.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">Status: {m.status}</p>
              <p className="text-sm text-muted-foreground">Wilayah: {m.region ?? "—"}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
