"use client";

import { Home } from "lucide-react";
import type { Match } from "@/types/match";
import { MatchCard } from "./match-card";

interface MatchListProps {
  matches: Match[];
  onInterested?: (matchId: string) => void;
  onPassed?: (matchId: string) => void;
}

/**
 * Eşleştirme listesi — kart grid layout
 * Responsive: 1 sütun mobil, 2 tablet, 3 desktop
 */
export function MatchList({ matches, onInterested, onPassed }: MatchListProps) {
  if (matches.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <Home className="h-12 w-12 mx-auto mb-3 text-gray-300" />
        <p className="text-sm">Henüz eşleşme bulunamadı.</p>
        <p className="text-xs text-gray-400 mt-1">
          Müşteri tercihleri ile uyumlu ilanlar otomatik eşleştirilecek.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {matches.map((match) => (
        <MatchCard
          key={match.id}
          match={match}
          onInterested={onInterested}
          onPassed={onPassed}
        />
      ))}
    </div>
  );
}
