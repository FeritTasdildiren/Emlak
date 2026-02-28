"use client";

import { ThumbsUp, X, Clock } from "lucide-react";
import type { Match, MatchStatus, MatchScoreDetails } from "@/types/match";
import { cn } from "@/lib/utils";

// --- Konfigürasyon ---

const MATCH_STATUS_CONFIG: Record<
  MatchStatus,
  { label: string; className: string }
> = {
  pending: { label: "Bekliyor", className: "bg-gray-100 text-gray-800" },
  interested: {
    label: "İlgileniyor",
    className: "bg-emerald-100 text-emerald-800",
  },
  passed: { label: "Geçildi", className: "bg-red-100 text-red-700" },
  contacted: {
    label: "İletişime Geçildi",
    className: "bg-blue-100 text-blue-800",
  },
  converted: {
    label: "Dönüşüm",
    className: "bg-purple-100 text-purple-800",
  },
};

// --- Yardımcı fonksiyonlar ---

/** Uyum skoru rengini hesapla */
function getScoreColor(score: number): {
  bg: string;
  text: string;
  bar: string;
} {
  if (score >= 85)
    return {
      bg: "bg-emerald-50",
      text: "text-emerald-700",
      bar: "bg-emerald-500",
    };
  if (score >= 70)
    return {
      bg: "bg-yellow-50",
      text: "text-yellow-700",
      bar: "bg-yellow-500",
    };
  return { bg: "bg-red-50", text: "text-red-700", bar: "bg-red-500" };
}

/** Fiyatı TL formatında göster */
function formatPrice(price: number): string {
  return new Intl.NumberFormat("tr-TR", {
    style: "currency",
    currency: "TRY",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(price);
}

/** Tarihten kısa göreli zaman üret */
function getShortRelativeTime(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffHour = Math.floor(diffMs / 3_600_000);
  const diffDay = Math.floor(diffHour / 24);

  if (diffHour < 1) return "az önce";
  if (diffHour < 24) return `${diffHour} saat önce`;
  if (diffDay < 7) return `${diffDay} gün önce`;
  return new Intl.DateTimeFormat("tr-TR", {
    day: "numeric",
    month: "short",
  }).format(date);
}

/** Notes JSON'dan skor detayları çözümle */
function parseScoreDetails(notes: string): MatchScoreDetails | null {
  try {
    return JSON.parse(notes) as MatchScoreDetails;
  } catch {
    return null;
  }
}

// --- Skor Detay Çubuğu ---

function ScoreBar({ label, score }: { label: string; score: number }) {
  const color = getScoreColor(score);
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500 w-14 shrink-0">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-1.5">
        <div
          className={cn("h-1.5 rounded-full transition-all", color.bar)}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className={cn("text-xs font-medium w-8 text-right", color.text)}>
        %{score}
      </span>
    </div>
  );
}

// --- Ana Bileşen ---

interface MatchCardProps {
  match: Match;
  onInterested?: (matchId: string) => void;
  onPassed?: (matchId: string) => void;
}

export function MatchCard({ match, onInterested, onPassed }: MatchCardProps) {
  const scoreColor = getScoreColor(match.score);
  const statusConfig = MATCH_STATUS_CONFIG[match.status];
  const scoreDetails = parseScoreDetails(match.notes);

  // Aksiyonlar sadece pending/contacted durumlarında aktif
  const canAct = match.status === "pending" || match.status === "contacted";

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow flex flex-col overflow-hidden">
      {/* Kart Üstü: Başlık + Fiyat + Durum */}
      <div className="p-4 pb-3">
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="min-w-0">
            <h4 className="font-bold text-gray-900 truncate text-sm">
              {match.property?.title ?? "İlan Bilgisi Yok"}
            </h4>
            <p className="text-xs text-gray-500 mt-0.5">
              {match.property?.district ?? "-"}
              {match.property?.rooms && ` • ${match.property.rooms}`}
            </p>
          </div>
          <span
            className={cn(
              "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium shrink-0",
              statusConfig.className
            )}
          >
            {statusConfig.label}
          </span>
        </div>

        {/* Fiyat */}
        <p className="text-lg font-bold text-indigo-600">
          {match.property ? formatPrice(match.property.price) : "-"}
        </p>
      </div>

      {/* Uyum Skoru */}
      <div className="px-4 py-3 border-t border-gray-100">
        <div className="flex justify-between items-center mb-1.5">
          <span className="text-xs font-medium text-gray-700">Uyum Skoru</span>
          <span className={cn("text-sm font-bold", scoreColor.text)}>
            %{match.score}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={cn("h-2 rounded-full transition-all", scoreColor.bar)}
            style={{ width: `${match.score}%` }}
          />
        </div>

        {/* Skor Detayları */}
        {scoreDetails && (
          <div className="mt-3 space-y-1.5">
            <ScoreBar label="Fiyat" score={scoreDetails.price_score} />
            <ScoreBar label="Konum" score={scoreDetails.location_score} />
            <ScoreBar label="Oda" score={scoreDetails.room_score} />
            <ScoreBar label="Alan" score={scoreDetails.area_score} />
          </div>
        )}
      </div>

      {/* Alt Kısım: Tarih + Aksiyonlar */}
      <div className="px-4 py-3 mt-auto border-t border-gray-100">
        {/* Eşleşme Tarihi */}
        <div className="flex items-center gap-1 text-xs text-gray-400 mb-3">
          <Clock className="h-3 w-3" />
          <span>{getShortRelativeTime(match.matched_at)}</span>
        </div>

        {/* Aksiyon Butonları */}
        {canAct ? (
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => onInterested?.(match.id)}
              className="flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-emerald-500 hover:bg-emerald-600 transition-colors"
            >
              <ThumbsUp className="h-4 w-4 mr-1.5" />
              İlgileniyorum
            </button>
            <button
              onClick={() => onPassed?.(match.id)}
              className="flex items-center justify-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 transition-colors"
            >
              <X className="h-4 w-4 mr-1.5" />
              Geç
            </button>
          </div>
        ) : (
          <div className="text-center">
            <span
              className={cn(
                "inline-flex items-center px-3 py-1.5 rounded text-xs font-medium",
                statusConfig.className
              )}
            >
              {statusConfig.label}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
