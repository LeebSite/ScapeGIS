import { redirect } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/img/logo_scapegis.svg" alt="Scapegis Logo" width={32} height={32} className="block" />
            <span className="font-kayak text-xl tracking-wide font-semibold text-[#01123E]">Scapegis</span>
          </div>
          <div className="flex items-center space-x-4">
            <Link href="/login">
              <Button variant="ghost">Masuk</Button>
            </Link>
            <Link href="/signup">
              <Button>Mulai</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <h1 className="text-5xl font-bold tracking-tight">
            Platform GIS Berbasis AI
            <br />
            untuk Pengembang Properti
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Alat GIS profesional bertenaga AI untuk membantu pengembang properti
            membuat keputusan cerdas dengan kecerdasan spasial.
          </p>
          <div className="flex items-center justify-center space-x-4">
            <Link href="/signup">
              <Button size="lg">Mulai Uji Coba Gratis</Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline">
                Masuk
              </Button>
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle>Peta Interaktif</CardTitle>
              <CardDescription>
                Alat pemetaan GIS yang kuat dengan visualisasi data real-time
              </CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Asisten AI</CardTitle>
              <CardDescription>
                Dapatkan wawasan dan rekomendasi instan dari chatbot AI kami
              </CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Akses Berbasis Peran</CardTitle>
              <CardDescription>
                Beranda khusus untuk admin dan pengembang properti
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t py-8 mt-16">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>&copy; 2024 Scapegis. Hak cipta dilindungi undang-undang.</p>
        </div>
      </footer>
    </div>
  );

}
