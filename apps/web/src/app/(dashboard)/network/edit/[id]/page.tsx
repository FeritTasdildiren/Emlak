"use client";

import { use } from "react";
import { useShowcaseDetail } from "@/hooks/use-showcases";
import { ShowcaseForm } from "@/components/network/showcase-form";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChevronLeft } from "lucide-react";
import { useRouter } from "next/navigation";

export default function ShowcaseEditPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { data: showcase, isLoading, isError } = useShowcaseDetail(id);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-9 w-9" />
          <Skeleton className="h-8 w-64" />
        </div>
        <Card>
          <CardContent className="pt-6 space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-24 w-full" />
          </CardContent>
        </Card>
        <div className="space-y-4">
          <Skeleton className="h-6 w-32" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-40 w-full rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (isError || !showcase) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <h2 className="text-xl font-bold text-gray-900">Vitrin bulunamadı</h2>
        <p className="text-gray-500 mt-2">
          Düzenlemek istediğiniz vitrin mevcut değil veya yetkiniz yok.
        </p>
        <Button
          variant="outline"
          className="mt-6"
          onClick={() => router.push("/network")}
        >
          <ChevronLeft className="mr-2 h-4 w-4" />
          Listeye Dön
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push("/network")}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-2xl font-bold text-gray-900">Vitrini Düzenle</h1>
      </div>

      <ShowcaseForm initialData={showcase} />
    </div>
  );
}
