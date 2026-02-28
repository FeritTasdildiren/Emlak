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
