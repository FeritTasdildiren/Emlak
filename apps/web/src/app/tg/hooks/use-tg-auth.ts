"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// ================================================================
// Types
// ================================================================

type TgAuthState = "loading" | "authenticated" | "error";

interface TgUser {
  id: string;
  full_name: string;
  role: string;
  avatar_url: string | null;
}

interface TgAuthResult {
  /** Auth durumu */
  state: TgAuthState;
  /** Authenticated kullanıcı bilgileri */
  user: TgUser | null;
  /** Hata mesajı (state === "error" ise) */
  error: string | null;
  /** Auth akışını yeniden dene */
  retry: () => void;
}

// ================================================================
// Constants
// ================================================================

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const TOKEN_KEY = "token";
const REFRESH_TOKEN_KEY = "refresh_token";
const TG_USER_KEY = "tg_user";

// ================================================================
// Helper — Token Storage
// ================================================================

function setTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

function clearTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(TG_USER_KEY);
}

function setStoredUser(user: TgUser): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TG_USER_KEY, JSON.stringify(user));
}

function getStoredUser(): TgUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(TG_USER_KEY);
    return raw ? (JSON.parse(raw) as TgUser) : null;
  } catch {
    return null;
  }
}

// ================================================================
// Helper — initDataRaw çekme
// ================================================================

async function getInitDataRaw(): Promise<string | null> {
  try {
    const sdk = await import("@telegram-apps/sdk-react");
    // SDK v3: retrieveRawInitData ile ham initData query string alınır
    return sdk.retrieveRawInitData() ?? null;
  } catch {
    return null;
  }
}

// ================================================================
// Helper — API istekleri
// ================================================================

interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: TgUser;
}

async function authenticateWithInitData(
  initDataRaw: string,
): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/telegram/mini-app/auth`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ init_data: initDataRaw }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      (errorData as { detail?: string }).detail ||
        `Auth başarısız: ${response.status}`,
    );
  }

  return response.json() as Promise<AuthResponse>;
}

async function refreshAccessToken(): Promise<AuthResponse | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      clearTokens();
      return null;
    }

    return response.json() as Promise<AuthResponse>;
  } catch {
    clearTokens();
    return null;
  }
}

// ================================================================
// Hook
// ================================================================

/**
 * Telegram Mini App auth hook.
 *
 * Akis:
 *   1. localStorage'da mevcut token var mı kontrol et
 *   2. Token varsa → authenticated
 *   3. Token yoksa → initDataRaw al → backend'e POST → JWT token al
 *   4. Token'ları localStorage'a kaydet
 *   5. Token expire olursa refresh mekanizması çalış
 *
 * Mevcut web panel auth sistemi (localStorage "token" key) ile uyumlu.
 */
export function useTgAuth(): TgAuthResult {
  const [state, setState] = useState<TgAuthState>("loading");
  const [user, setUser] = useState<TgUser | null>(null);
  const [error, setError] = useState<string | null>(null);
  const authAttempted = useRef(false);

  const authenticate = useCallback(async () => {
    setState("loading");
    setError(null);

    try {
      // 1. Mevcut token kontrolü
      const existingToken = getAccessToken();
      const existingUser = getStoredUser();

      if (existingToken && existingUser) {
        // Token var — validate et (basit kontrol: expired mi?)
        try {
          const payload = JSON.parse(atob(existingToken.split(".")[1]));
          const exp = (payload as { exp?: number }).exp;
          if (exp && exp * 1000 > Date.now()) {
            // Token hâlâ geçerli
            setUser(existingUser);
            setState("authenticated");
            return;
          }
        } catch {
          // Token parse edilemedi — devam et
        }

        // Token expired — refresh dene
        const refreshResult = await refreshAccessToken();
        if (refreshResult) {
          setTokens(refreshResult.access_token, refreshResult.refresh_token);
          setStoredUser(refreshResult.user);
          setUser(refreshResult.user);
          setState("authenticated");
          return;
        }
      }

      // 2. initDataRaw al
      const initDataRaw = await getInitDataRaw();
      if (!initDataRaw) {
        throw new Error(
          "Telegram bağlantı bilgileri alınamadı. Lütfen Mini App'i yeniden açın.",
        );
      }

      // 3. Backend'e auth isteği gönder
      const authResult = await authenticateWithInitData(initDataRaw);

      // 4. Token'ları kaydet
      setTokens(authResult.access_token, authResult.refresh_token);
      setStoredUser(authResult.user);
      setUser(authResult.user);
      setState("authenticated");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Giriş yapılırken bir hata oluştu.";
      setError(message);
      setState("error");
    }
  }, []);

  useEffect(() => {
    // Sadece bir kez auth dene
    if (authAttempted.current) return;
    authAttempted.current = true;
    authenticate();
  }, [authenticate]);

  const retry = useCallback(() => {
    authAttempted.current = false;
    authenticate();
  }, [authenticate]);

  return { state, user, error, retry };
}
