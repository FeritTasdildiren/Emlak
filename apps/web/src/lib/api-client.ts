const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  statusText: string;
  requestId?: string;
  detail?: string;
  title?: string;
  type?: string;

  constructor(
    message: string,
    status: number,
    statusText: string,
    requestId?: string,
    detail?: string,
    title?: string,
    type?: string
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.statusText = statusText;
    this.requestId = requestId;
    this.detail = detail;
    this.title = title;
    this.type = type;
  }
}

type RequestOptions = RequestInit & {
  headers?: Record<string, string>;
};

// ---------------------------------------------------------------------------
// Token refresh mekanizmasi — 401 interceptor
// ---------------------------------------------------------------------------

/** Refresh endpoint'leri interceptor'dan haric tutulur (sonsuz dongu riski). */
const AUTH_EXCLUDED_ENDPOINTS = ["/auth/refresh", "/auth/login", "/auth/register"];

/**
 * Eslesen refresh istegi varsa tekrarlamamak icin tek bir Promise tutulur.
 * Birden fazla 401 alinirsa hepsi ayni refresh sonucunu bekler.
 */
let refreshPromise: Promise<string | null> | null = null;

/**
 * Refresh token ile yeni access token alir.
 * Basarili: yeni access_token string doner ve localStorage guncellenir.
 * Basarisiz: null doner ve localStorage temizlenir + /login redirect yapilir.
 */
async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null;
  if (!refreshToken) {
    handleAuthFailure();
    return null;
  }

  try {
    const response = await fetch(`${BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      handleAuthFailure();
      return null;
    }

    const data = await response.json();
    if (typeof window !== "undefined") {
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
    }
    return data.access_token as string;
  } catch {
    handleAuthFailure();
    return null;
  }
}

/** Auth token'lari temizle ve login sayfasina yonlendir. */
function handleAuthFailure(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
    // Zaten login sayfasindaysak redirect yapma
    if (!window.location.pathname.startsWith("/login") && !window.location.pathname.startsWith("/auth")) {
      window.location.href = "/login";
    }
  }
}

// ---------------------------------------------------------------------------
// Core request fonksiyonu — 401 interceptor dahil
// ---------------------------------------------------------------------------

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  // Client-side only: get token from localStorage
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const config: RequestInit = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, config);
    const requestId = response.headers.get("X-Request-ID") || undefined;

    // 401 Interceptor — auth endpoint'leri haric
    if (response.status === 401 && !AUTH_EXCLUDED_ENDPOINTS.some((ep) => endpoint.startsWith(ep))) {
      // Eslesme varsa mevcut refresh promise'i bekle, yoksa yenisini baslat
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
      }

      const newToken = await refreshPromise;
      if (newToken) {
        // Yeni token ile orijinal istegi tekrarla
        const retryHeaders = {
          ...headers,
          Authorization: `Bearer ${newToken}`,
        };
        const retryConfig: RequestInit = { ...options, headers: retryHeaders };
        const retryResponse = await fetch(`${BASE_URL}${endpoint}`, retryConfig);
        const retryRequestId = retryResponse.headers.get("X-Request-ID") || undefined;

        if (!retryResponse.ok) {
          let errorData;
          try {
            errorData = await retryResponse.json();
          } catch {
            errorData = {};
          }
          const message = errorData.detail || errorData.message || `API Error: ${retryResponse.status} ${retryResponse.statusText}`;
          throw new ApiError(message, retryResponse.status, retryResponse.statusText, retryRequestId, errorData.detail, errorData.title, errorData.type);
        }

        if (retryResponse.status === 204) {
          return {} as T;
        }
        return await retryResponse.json();
      }

      // Refresh basarisiz — orijinal 401 hatasiyla devam et
      throw new ApiError(
        "Oturumunuz sona erdi. Lütfen tekrar giriş yapın.",
        401,
        "Unauthorized",
        requestId
      );
    }

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = {};
      }

      // RFC 7807 fields or fallback
      const message = errorData.detail || errorData.message || `API Error: ${response.status} ${response.statusText}`;
      const detail = errorData.detail;
      const title = errorData.title;
      const type = errorData.type;

      throw new ApiError(
        message,
        response.status,
        response.statusText,
        requestId,
        detail,
        title,
        type
      );
    }

    // Handle empty responses (e.g., 204 No Content)
    if (response.status === 204) {
      return {} as T;
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    // Network errors or other issues not related to API response
    console.error("API Request Failed:", error);
    throw new ApiError(
      error instanceof Error ? error.message : "Bilinmeyen bir hata oluştu",
      500,
      "Internal Error"
    );
  }
}

/**
 * Multipart/form-data POST istegi — dosya yukleme icin.
 * Content-Type header'i GONDERILMEZ (browser FormData boundary'yi otomatik ekler).
 */
async function requestFormData<T>(endpoint: string, formData: FormData): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const headers: Record<string, string> = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: "POST",
      headers,
      body: formData,
    });
    const requestId = response.headers.get("X-Request-ID") || undefined;

    // 401 Interceptor — FormData istekleri icin de gecerli
    if (response.status === 401 && !AUTH_EXCLUDED_ENDPOINTS.some((ep) => endpoint.startsWith(ep))) {
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
      }

      const newToken = await refreshPromise;
      if (newToken) {
        const retryHeaders: Record<string, string> = {
          Authorization: `Bearer ${newToken}`,
        };
        const retryResponse = await fetch(`${BASE_URL}${endpoint}`, {
          method: "POST",
          headers: retryHeaders,
          body: formData,
        });
        const retryRequestId = retryResponse.headers.get("X-Request-ID") || undefined;

        if (!retryResponse.ok) {
          let errorData;
          try {
            errorData = await retryResponse.json();
          } catch {
            errorData = {};
          }
          const message = errorData.detail || errorData.message || `API Error: ${retryResponse.status} ${retryResponse.statusText}`;
          throw new ApiError(message, retryResponse.status, retryResponse.statusText, retryRequestId, errorData.detail, errorData.title, errorData.type);
        }

        if (retryResponse.status === 204) {
          return {} as T;
        }
        return await retryResponse.json();
      }

      throw new ApiError(
        "Oturumunuz sona erdi. Lütfen tekrar giriş yapın.",
        401,
        "Unauthorized",
        requestId
      );
    }

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = {};
      }

      const message = errorData.detail || errorData.message || `API Error: ${response.status} ${response.statusText}`;
      const detail = errorData.detail;
      const title = errorData.title;
      const type = errorData.type;

      throw new ApiError(message, response.status, response.statusText, requestId, detail, title, type);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    console.error("API FormData Request Failed:", error);
    throw new ApiError(
      error instanceof Error ? error.message : "Bilinmeyen bir hata oluştu",
      500,
      "Internal Error"
    );
  }
}

export const api = {
  get: <T>(endpoint: string, options?: RequestOptions) => request<T>(endpoint, { ...options, method: "GET" }),
  post: <T>(endpoint: string, body: unknown, options?: RequestOptions) => request<T>(endpoint, { ...options, method: "POST", body: JSON.stringify(body) }),
  put: <T>(endpoint: string, body: unknown, options?: RequestOptions) => request<T>(endpoint, { ...options, method: "PUT", body: JSON.stringify(body) }),
  patch: <T>(endpoint: string, body: unknown, options?: RequestOptions) => request<T>(endpoint, { ...options, method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(endpoint: string, options?: RequestOptions) => request<T>(endpoint, { ...options, method: "DELETE" }),
  postFormData: <T>(endpoint: string, formData: FormData) => requestFormData<T>(endpoint, formData),
};
