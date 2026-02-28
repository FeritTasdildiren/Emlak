"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { toast } from "@/components/ui/toast";

interface DeleteShowcaseButtonProps {
  showcaseId: string;
}

export function DeleteShowcaseButton({ showcaseId }: DeleteShowcaseButtonProps) {
  const router = useRouter();
  const [isDeleting, setIsDeleting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleConfirm = useCallback(async () => {
    setIsDeleting(true);
    // Mock delete API call
    await new Promise((resolve) => setTimeout(resolve, 600));
    console.log(`[Mock API] Deleted showcase: ${showcaseId}`);
    setIsDeleting(false);
    setShowConfirm(false);
    toast("Vitrin başarıyla silindi!");
    router.push("/network");
  }, [showcaseId, router]);

  return (
    <>
      <Button
        variant="destructive"
        size="sm"
        className="gap-1.5"
        onClick={() => setShowConfirm(true)}
        disabled={isDeleting}
        loading={isDeleting}
      >
        <Trash2 className="h-4 w-4" />
        Vitrini Sil
      </Button>

      <ConfirmDialog
        open={showConfirm}
        title="Vitrini Sil"
        description="Bu vitrini silmek istediğinize emin misiniz? Bu işlem geri alınamaz."
        confirmLabel="Sil"
        cancelLabel="Vazgeç"
        variant="danger"
        loading={isDeleting}
        onConfirm={handleConfirm}
        onCancel={() => setShowConfirm(false)}
      />
    </>
  );
}
