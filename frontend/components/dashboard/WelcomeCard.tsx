import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useAuthStore } from "@/lib/store";

export function WelcomeCard() {
  const { user } = useAuthStore();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Selamat datang kembali, {user?.name ?? "Pengguna"}</CardTitle>
        <CardDescription>Status akun Anda: {user ? "Aktif" : "Tamu"}</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">Gunakan beranda untuk mengelola proyek, peta, dan langganan.</p>
      </CardContent>
    </Card>
  );
}
