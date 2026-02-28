// ================================================================
// Ayarlar sayfası tip tanımları
// ================================================================

/** GET /auth/me yanıtı */
export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  role: string;
  office_id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Profil güncelleme formu değerleri */
export interface ProfileFormValues {
  full_name: string;
  phone: string;
}

/** Şifre değiştirme formu değerleri */
export interface ChangePasswordFormValues {
  current_password: string;
  new_password: string;
  new_password_confirm: string;
}

/** Şifre değiştirme API isteği */
export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

/** Bildirim tercihleri (localStorage) */
export interface NotificationPreferences {
  email_notifications: boolean;
  telegram_notifications: boolean;
  match_notifications: boolean;
  valuation_notifications: boolean;
  language: string;
}

/** Varsayılan bildirim tercihleri */
export const DEFAULT_NOTIFICATION_PREFERENCES: NotificationPreferences = {
  email_notifications: true,
  telegram_notifications: true,
  match_notifications: true,
  valuation_notifications: true,
  language: "tr",
};

/** localStorage anahtarı */
export const NOTIFICATION_PREFS_KEY = "emlak_notification_prefs";
