"use client";

import {
  type ReactNode,
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

// ================================================================
// Types
// ================================================================

type TgSdkState = "loading" | "ready" | "error" | "not-telegram";

interface TgProviderContextValue {
  /** SDK durumu */
  state: TgSdkState;
  /** Hata mesajı (state === "error" ise) */
  error: string | null;
}

const TgProviderContext = createContext<TgProviderContextValue>({
  state: "loading",
  error: null,
});

// ================================================================
// Hook
// ================================================================

export function useTgSdk(): TgProviderContextValue {
  return useContext(TgProviderContext);
}

// ================================================================
// Provider
// ================================================================

interface TgProviderProps {
  children: ReactNode;
}

/**
 * Telegram Mini App SDK Provider.
 *
 * - SDK init() ile Telegram Web App kontekstini başlatır.
 * - viewport.expand() ile tam ekran yapar.
 * - miniApp, themeParams, viewport CSS variable'larını bind eder.
 * - Telegram dışında açılırsa "not-telegram" state'i döner.
 * - SDK yüklenene kadar splash/loading gösterir.
 */
export function TgProvider({ children }: TgProviderProps) {
  const [state, setState] = useState<TgSdkState>("loading");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cleanup: (() => void) | undefined;

    async function initSdk() {
      try {
        // Dynamic import — SDK sadece client-side'da yüklenir
        const sdk = await import("@telegram-apps/sdk-react");

        // SDK'yi başlat
        cleanup = sdk.init({ acceptCustomStyles: true });

        // Mini App mount
        if (sdk.miniApp.mountSync.isAvailable()) {
          sdk.miniApp.mountSync();
        }

        // Mini App CSS variables bind
        if (sdk.miniApp.bindCssVars.isAvailable()) {
          sdk.miniApp.bindCssVars();
        }

        // Theme params mount + CSS variables bind
        if (sdk.themeParams.mountSync.isAvailable()) {
          sdk.themeParams.mountSync();
        }
        if (sdk.themeParams.bindCssVars.isAvailable()) {
          sdk.themeParams.bindCssVars();
        }

        // Viewport mount (async) + expand + CSS variables bind
        if (sdk.viewport.mount.isAvailable()) {
          await sdk.viewport.mount();
        }
        if (sdk.viewport.expand.isAvailable()) {
          sdk.viewport.expand();
        }
        if (sdk.viewport.bindCssVars.isAvailable()) {
          sdk.viewport.bindCssVars();
        }

        // Mini App hazır sinyali gönder
        if (sdk.miniApp.ready.isAvailable()) {
          sdk.miniApp.ready();
        }

        setState("ready");
      } catch (err) {
        // SDK init başarısız — büyük ihtimalle Telegram dışında açılmış
        const message =
          err instanceof Error ? err.message : "SDK başlatılamadı";

        // Telegram dışında açıldığında tipik hatalar
        if (
          message.includes("ERR_RETRIEVE_LP_FAILED") ||
          message.includes("LaunchParams") ||
          message.includes("Unable to retrieve")
        ) {
          setState("not-telegram");
          setError("Bu uygulama sadece Telegram içinden açılabilir.");
        } else {
          setState("error");
          setError(message);
        }
      }
    }

    initSdk();

    return () => {
      cleanup?.();
    };
  }, []);

  // --- Loading State ---
  if (state === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-orange-200 border-t-orange-600" />
          <p className="text-sm text-gray-500">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  // --- Not Telegram State ---
  if (state === "not-telegram") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-6">
        <div className="max-w-sm rounded-2xl bg-white p-8 text-center shadow-lg">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-orange-100">
            <svg
              className="h-8 w-8 text-orange-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
          </div>
          <h2 className="mb-2 text-lg font-bold text-gray-900">
            Telegram Gerekli
          </h2>
          <p className="text-sm text-gray-500">
            Bu uygulama sadece Telegram üzerinden erişilebilir. Lütfen
            Telegram&apos;dan Mini App olarak açın.
          </p>
        </div>
      </div>
    );
  }

  // --- Error State ---
  if (state === "error") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 px-6">
        <div className="max-w-sm rounded-2xl bg-white p-8 text-center shadow-lg">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
            <svg
              className="h-8 w-8 text-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>
          <h2 className="mb-2 text-lg font-bold text-gray-900">
            Bir Hata Oluştu
          </h2>
          <p className="text-sm text-gray-500">{error}</p>
        </div>
      </div>
    );
  }

  // --- Ready State ---
  return (
    <TgProviderContext.Provider value={{ state, error }}>
      {children}
    </TgProviderContext.Provider>
  );
}
