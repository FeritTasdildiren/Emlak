"use client";

import { use } from "react";
import { notFound } from "next/navigation";
import { ChevronLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ShowcaseForm } from "@/components/network/showcase-form";
import { useShowcaseDetail } from "@/hooks/use-showcases";
import { DeleteShowcaseButton } from "@/components/network/delete-showcase-button";

interface EditShowcasePageProps {
  params: Promise<{ id: string }>;
}

export default function EditShowcasePage(props: EditShowcasePageProps) {
  const params = use(props.params);
  const { data: showcase, isLoading, error } = useShowcaseDetail(params.id);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error || !showcase) {
    notFound();
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Link href="/network">
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <ChevronLeft className="h-4 w-4" />
                <span className="sr-only">Geri</span>
              </Button>
            </Link>
            <h1 className="text-2xl font-bold text-gray-900">
              Vitrin Düzenle: {showcase.title}
            </h1>
          </div>
          <DeleteShowcaseButton showcaseId={showcase.id} />
        </div>
        <p className="text-sm text-gray-500 max-w-2xl pl-10">
          Vitrininizdeki ilanları güncelleyebilir veya vitrin temasını
          değiştirebilirsiniz.
        </p>
      </div>

      <div className="pl-10">
        <ShowcaseForm initialData={showcase} />
      </div>
    </div>
  );
}
