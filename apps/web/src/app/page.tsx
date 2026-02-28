import type { Metadata } from "next";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { LandingRedirect } from "./landing-redirect";

export const metadata: Metadata = {
  title: "Ana Sayfa",
  description: "Türkiye'nin en gelişmiş emlak teknoloji platformu. Portföy yönetimi, CRM, değerleme ve akıllı eşleşmeler ile işinizi dijitalleştirin.",
};

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <LandingRedirect />
      <header className="px-6 py-4 flex items-center justify-between border-b bg-white/50 backdrop-blur-sm sticky top-0 z-50">
        <span className="text-xl font-bold text-blue-600">EmlakTech</span>
        <div className="flex gap-4">
          <Link href="/login">
            <Button variant="ghost">Giriş Yap</Button>
          </Link>
          <Link href="/register">
            <Button>Kayıt Ol</Button>
          </Link>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center text-center px-4 py-20 bg-gradient-to-b from-blue-50 to-white">
        <h1 className="text-5xl font-extrabold tracking-tight text-gray-900 sm:text-6xl mb-6">
          Geleceğin Emlak <span className="text-blue-600">Platformu</span>
        </h1>
        <p className="max-w-2xl text-lg text-gray-600 mb-10">
          Tüm emlak süreçlerinizi tek bir yerden yönetin. Müşteri takibi, portföy yönetimi ve yapay zeka destekli değerleme araçları ile işinizi büyütün.
        </p>
        <div className="flex flex-col sm:flex-row gap-4">
          <Link href="/register">
            <Button size="lg" className="px-8 text-lg w-full sm:w-auto">Hemen Başla</Button>
          </Link>
          <Link href="/login">
            <Button variant="outline" size="lg" className="px-8 text-lg w-full sm:w-auto">Demoyu İncele</Button>
          </Link>
        </div>
      </main>

      <footer className="py-6 border-t text-center text-gray-500 text-sm">
        &copy; {new Date().getFullYear()} EmlakTech. Tüm hakları saklıdır.
      </footer>
    </div>
  );
}