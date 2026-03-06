import { useRouter } from "next/navigation";
import { usePropertyMatches } from "@/hooks/use-property-matches";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/utils";
import { MatchStatus } from "@/types/match";

interface PropertyMatchesModalProps {
  isOpen: boolean;
  onClose: () => void;
  propertyId: string;
}

const statusConfig: Record<
  MatchStatus,
  { label: string; variant: "success" | "default" | "warning" | "secondary" }
> = {
  pending: { label: "Bekliyor", variant: "warning" },
  interested: { label: "İlgileniyor", variant: "success" },
  passed: { label: "Geçti", variant: "secondary" },
  contacted: { label: "İletişime Geçildi", variant: "default" },
  converted: { label: "Dönüştürüldü", variant: "success" },
};

export function PropertyMatchesModal({
  isOpen,
  onClose,
  propertyId,
}: PropertyMatchesModalProps) {
  const router = useRouter();
  const { matches, isLoading, isError } = usePropertyMatches(propertyId);

  const getScoreColor = (score: number) => {
    if (score >= 80) return "bg-green-100 text-green-700 border-green-200";
    if (score >= 60) return "bg-blue-100 text-blue-700 border-blue-200";
    if (score >= 40) return "bg-yellow-100 text-yellow-700 border-yellow-200";
    return "bg-red-100 text-red-700 border-red-200";
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Eşleşen Müşteriler"
      className="max-w-3xl"
    >
      <div className="space-y-4">
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-16 w-full rounded-lg" />
            ))}
          </div>
        ) : isError ? (
          <div className="py-8 text-center text-red-500">
            Eşleşmeler yüklenirken bir hata oluştu.
          </div>
        ) : matches.length === 0 ? (
          <div className="py-12 text-center text-gray-500 italic">
            Henüz eşleştirme yapılmamış
          </div>
        ) : (
          <div className="divide-y border rounded-lg overflow-hidden">
            {matches.map((match) => {
              const status = statusConfig[match.status] || statusConfig.pending;
              return (
                <div
                  key={match.id}
                  className="p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                  <div className="flex flex-col gap-1">
                    <button
                      onClick={() =>
                        router.push(`/dashboard/customers/${match.customer_id}`)
                      }
                      className="text-left font-semibold text-blue-600 hover:underline"
                    >
                      {match.customer_name || "Bilinmeyen Müşteri"}
                    </button>
                    <div className="text-xs text-gray-500">
                      {formatDate(match.matched_at)}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div
                      className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getScoreColor(
                        match.score
                      )}`}
                    >
                      %{match.score}
                    </div>
                    <Badge variant={status.variant}>{status.label}</Badge>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Modal>
  );
}
