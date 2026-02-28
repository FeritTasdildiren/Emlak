"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { toast } from "@/components/ui/toast";
import {
  DEFAULT_NOTIFICATION_PREFERENCES,
  NOTIFICATION_PREFS_KEY,
  type NotificationPreferences,
} from "@/types/settings";

// ================================================================
// Toggle Bileşeni
// ================================================================

function Toggle({
  checked,
  onChange,
  label,
  description,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
  label: string;
  description?: string;
}) {
  return (
    <label className="flex items-center justify-between gap-4 py-3 cursor-pointer">
      <div className="space-y-0.5">
        <p className="text-sm font-medium text-gray-900">{label}</p>
        {description && (
          <p className="text-xs text-gray-500">{description}</p>
        )}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2 ${
          checked ? "bg-blue-600" : "bg-gray-200"
        }`}
      >
        <span
          className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-lg ring-0 transition-transform duration-200 ease-in-out ${
            checked ? "translate-x-5" : "translate-x-0"
          }`}
        />
      </button>
    </label>
  );
}

// ================================================================
// localStorage yardımcı fonksiyonları
// ================================================================

function loadPreferences(): NotificationPreferences {
  if (typeof window === "undefined") return DEFAULT_NOTIFICATION_PREFERENCES;
  try {
    const raw = localStorage.getItem(NOTIFICATION_PREFS_KEY);
    if (!raw) return DEFAULT_NOTIFICATION_PREFERENCES;
    const parsed = JSON.parse(raw) as Partial<NotificationPreferences>;
    return { ...DEFAULT_NOTIFICATION_PREFERENCES, ...parsed };
  } catch {
    return DEFAULT_NOTIFICATION_PREFERENCES;
  }
}

function savePreferences(prefs: NotificationPreferences): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(NOTIFICATION_PREFS_KEY, JSON.stringify(prefs));
  } catch {
    // localStorage dolu olabilir — sessizce geç
  }
}

// ================================================================
// Bildirim Ayarları Bileşeni
// ================================================================

export function NotificationSettings() {
  const [prefs, setPrefs] = useState<NotificationPreferences>(DEFAULT_NOTIFICATION_PREFERENCES);
  const [isDirty, setIsDirty] = useState(false);

  // İlk yüklemede localStorage'dan oku
  useEffect(() => {
    setPrefs(loadPreferences());
  }, []);

  const updatePref = useCallback(
    <K extends keyof NotificationPreferences>(
      key: K,
      value: NotificationPreferences[K]
    ) => {
      setPrefs((prev) => ({ ...prev, [key]: value }));
      setIsDirty(true);
    },
    []
  );

  const handleSave = () => {
    savePreferences(prefs);
    setIsDirty(false);
    toast("Bildirim tercihleri kaydedildi", "success");
  };

  return (
    <div className="space-y-6">
      {/* Bildirim Tercihleri */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Bildirim Tercihleri</CardTitle>
          <CardDescription>
            Hangi bildirimleri almak istediğinizi seçin.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="divide-y divide-gray-100">
            <Toggle
              checked={prefs.email_notifications}
              onChange={(v) => updatePref("email_notifications", v)}
              label="E-posta Bildirimleri"
              description="Önemli güncellemeler ve raporlar e-posta ile gönderilsin"
            />
            <Toggle
              checked={prefs.telegram_notifications}
              onChange={(v) => updatePref("telegram_notifications", v)}
              label="Telegram Bildirimleri"
              description="Anlık bildirimler Telegram üzerinden gönderilsin"
            />
            <Toggle
              checked={prefs.match_notifications}
              onChange={(v) => updatePref("match_notifications", v)}
              label="Eşleştirme Bildirimleri"
              description="Müşteri-ilan eşleşmelerinde bildirim alın"
            />
            <Toggle
              checked={prefs.valuation_notifications}
              onChange={(v) => updatePref("valuation_notifications", v)}
              label="Değerleme Bildirimleri"
              description="Değerleme tamamlandığında bildirim alın"
            />
          </div>
        </CardContent>
      </Card>

      {/* Dil Tercihi */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Dil Tercihi</CardTitle>
          <CardDescription>Uygulama dilini seçin.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-full max-w-xs items-center rounded-lg border border-input bg-gray-50 px-3 py-2 text-sm text-gray-500">
              <span className="mr-2">🇹🇷</span>
              Türkçe
            </div>
            <span className="text-xs text-gray-400">(Şu an tek desteklenen dil)</span>
          </div>
        </CardContent>
      </Card>

      {/* Kaydet butonu */}
      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={!isDirty}>
          Tercihleri Kaydet
        </Button>
      </div>
    </div>
  );
}
