import { Metadata } from "next";
import { ChevronLeft } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ShowcaseForm } from "@/components/network/showcase-form";

export const metadata: Metadata = {
  title: "Yeni Vitrin Oluştur | EmlakTech",
  description: "Portföyünüzden yeni bir vitrin sayfası oluşturun.",
};

export default function CreateShowcasePage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <Link href="/network">
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <ChevronLeft className="h-4 w-4" />
              <span className="sr-only">Geri</span>
            </Button>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">
            Yeni Vitrin Oluştur
          </h1>
        </div>
        <p className="text-sm text-gray-500 max-w-2xl pl-10">
          Müşterilerinizle veya sosyal medyada paylaşabileceğiniz özel bir
          vitrin sayfası oluşturun. Hangi ilanların gösterileceğini seçin ve
          sayfa temasını belirleyin.
        </p>
      </div>

      <div className="pl-10">
        <ShowcaseForm />
      </div>
    </div>
  );
}
