"use client";

import { useState } from "react";
import { Phone, Mail, Users, FileText, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { CustomerNote, NoteType } from "@/hooks/use-customer-detail";
import { cn } from "@/lib/utils";

// --- Not tipi konfigürasyonları ---

const NOTE_TYPE_CONFIG: Record<
  NoteType,
  { label: string; icon: typeof Phone; className: string }
> = {
  general: {
    label: "Genel",
    icon: FileText,
    className: "bg-gray-200 text-gray-600",
  },
  call: {
    label: "Arama",
    icon: Phone,
    className: "bg-blue-100 text-blue-600",
  },
  meeting: {
    label: "Toplantı",
    icon: Users,
    className: "bg-purple-100 text-purple-600",
  },
  email: {
    label: "E-posta",
    icon: Mail,
    className: "bg-amber-100 text-amber-600",
  },
};

// --- Yardımcı fonksiyonlar ---

/** Tarihten göreli zaman dizesi üretir */
function getRelativeTime(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60_000);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);
  const diffWeek = Math.floor(diffDay / 7);
  const diffMonth = Math.floor(diffDay / 30);

  if (diffMin < 1) return "az önce";
  if (diffMin < 60) return `${diffMin} dakika önce`;
  if (diffHour < 24) return `${diffHour} saat önce`;
  if (diffDay < 7) return `${diffDay} gün önce`;
  if (diffWeek < 4) return `${diffWeek} hafta önce`;
  if (diffMonth < 12) return `${diffMonth} ay önce`;
  return new Intl.DateTimeFormat("tr-TR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(date);
}

/** İsim baş harflerini çıkar */
function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

// --- Bileşen ---

interface CustomerNotesProps {
  notes: CustomerNote[];
  onAddNote?: (content: string, type: NoteType) => void;
}

export function CustomerNotes({ notes, onAddNote }: CustomerNotesProps) {
  const [newNote, setNewNote] = useState("");
  const [noteType, setNoteType] = useState<NoteType>("general");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim()) return;

    onAddNote?.(newNote.trim(), noteType);
    setNewNote("");
    setNoteType("general");
  };

  return (
    <div className="flow-root">
      {/* Not Ekleme Formu */}
      <div className="mb-8">
        <form onSubmit={handleSubmit}>
          <div className="flex gap-3">
            {/* Avatar */}
            <div className="flex-shrink-0">
              <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-sm">
                FA
              </div>
            </div>

            {/* Form Alanları */}
            <div className="min-w-0 flex-1">
              <textarea
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                rows={3}
                className="shadow-sm block w-full focus:ring-blue-500 focus:border-blue-500 sm:text-sm border border-gray-300 rounded-md p-3 resize-none"
                placeholder="Yeni bir not ekle..."
              />

              {/* Not tipi seçici + Gönder */}
              <div className="mt-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">Tip:</span>
                  {(
                    Object.entries(NOTE_TYPE_CONFIG) as [
                      NoteType,
                      (typeof NOTE_TYPE_CONFIG)[NoteType],
                    ][]
                  ).map(([type, config]) => {
                    const Icon = config.icon;
                    return (
                      <button
                        key={type}
                        type="button"
                        onClick={() => setNoteType(type)}
                        className={cn(
                          "inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors",
                          noteType === type
                            ? config.className
                            : "bg-gray-50 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                        )}
                      >
                        <Icon className="h-3 w-3" />
                        {config.label}
                      </button>
                    );
                  })}
                </div>

                <Button type="submit" size="sm" disabled={!newNote.trim()}>
                  <Send className="h-4 w-4 mr-1" />
                  Not Ekle
                </Button>
              </div>
            </div>
          </div>
        </form>
      </div>

      {/* Not Listesi (Timeline) */}
      {notes.length > 0 ? (
        <ul role="list" className="-mb-8">
          {notes.map((note, idx) => {
            const config = NOTE_TYPE_CONFIG[note.type];
            const Icon = config.icon;
            const isLast = idx === notes.length - 1;

            return (
              <li key={note.id}>
                <div className="relative pb-8">
                  {/* Timeline çizgisi */}
                  {!isLast && (
                    <span
                      className="absolute top-5 left-5 -ml-px h-full w-0.5 bg-gray-200"
                      aria-hidden="true"
                    />
                  )}

                  <div className="relative flex space-x-3">
                    {/* Avatar / İkon */}
                    <div
                      className={cn(
                        "h-10 w-10 rounded-full flex items-center justify-center ring-8 ring-white",
                        note.author === "Sistem"
                          ? "bg-gray-200"
                          : "bg-indigo-100"
                      )}
                    >
                      {note.author === "Sistem" ? (
                        <Icon className="h-4 w-4 text-gray-500" />
                      ) : (
                        <span className="text-indigo-600 font-medium text-xs">
                          {getInitials(note.author)}
                        </span>
                      )}
                    </div>

                    {/* İçerik */}
                    <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                      <div>
                        <p className="text-sm text-gray-500">
                          <span className="font-medium text-gray-900">
                            {note.author}
                          </span>
                          {" — "}
                          <span
                            className={cn(
                              "inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium",
                              config.className
                            )}
                          >
                            <Icon className="h-3 w-3" />
                            {config.label}
                          </span>
                        </p>
                        <div className="mt-2 text-sm text-gray-700 bg-gray-50 p-3 rounded-md border border-gray-100">
                          <p>{note.content}</p>
                        </div>
                      </div>

                      {/* Tarih */}
                      <div className="text-right text-sm whitespace-nowrap text-gray-500">
                        <time dateTime={note.created_at}>
                          {getRelativeTime(note.created_at)}
                        </time>
                      </div>
                    </div>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      ) : (
        <div className="text-center py-12 text-gray-500">
          <FileText className="h-12 w-12 mx-auto mb-3 text-gray-300" />
          <p className="text-sm">Henüz not eklenmemiş.</p>
        </div>
      )}
    </div>
  );
}
