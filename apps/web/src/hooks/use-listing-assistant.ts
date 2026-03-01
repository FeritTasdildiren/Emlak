import { useState, useEffect, useCallback } from 'react';
import { ListingFormData, ListingTextResponse, ToneInfo } from '@/types/listing';
import { listingsApi } from '@/lib/api/listings';
import { ApiError } from '@/lib/api-client';

/**
 * API hata koduna göre kullanıcı dostu Türkçe mesaj döndürür.
 */
function getErrorMessage(err: unknown, context: 'generate' | 'regenerate' | 'tones'): string {
  if (err instanceof ApiError) {
    // Kota aşımı (429 veya backend kota mesajı)
    if (err.status === 429 || err.detail?.includes('kota') || err.detail?.includes('quota')) {
      return 'Aylık ilan metni üretim kotanız doldu. Plan yükseltmesi yapabilirsiniz.';
    }
    // Validasyon hatası (422 — eksik/hatalı alan)
    if (err.status === 422) {
      return 'Form bilgilerinde eksik veya hatalı alan var. Lütfen tüm zorunlu alanları kontrol edin.';
    }
    // Yetkilendirme hatası
    if (err.status === 401) {
      return 'Oturumunuz sona ermiş. Lütfen tekrar giriş yapın.';
    }
    // Erişim yetkisi yok
    if (err.status === 403) {
      return 'Bu işlem için yetkiniz bulunmuyor. Plan yükseltmesi gerekebilir.';
    }
    // Sunucu hatası
    if (err.status >= 500) {
      return 'Sunucuda bir sorun oluştu. Lütfen birkaç dakika sonra tekrar deneyin.';
    }
  }

  // Ağ hatası
  if (err instanceof TypeError && (err as TypeError).message.includes('fetch')) {
    return 'İnternet bağlantınızı kontrol edin ve tekrar deneyin.';
  }

  const contextMessages: Record<typeof context, string> = {
    generate: 'İlan metni oluşturulurken bir hata oluştu. Lütfen tekrar deneyin.',
    regenerate: 'İlan metni yeniden üretilirken bir hata oluştu. Lütfen tekrar deneyin.',
    tones: 'Ton listesi yüklenemedi. Lütfen sayfayı yenileyin.',
  };

  return contextMessages[context];
}

export function useListingAssistant() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<ListingTextResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tones, setTones] = useState<ToneInfo[]>([]);
  const [isLoadingTones, setIsLoadingTones] = useState(false);

  const loadTones = useCallback(async () => {
    setIsLoadingTones(true);
    try {
      const data = await listingsApi.getAvailableTones();
      setTones(data);
    } catch (err) {
      console.error("Tonlar yüklenirken hata oluştu:", err);
      setError(getErrorMessage(err, 'tones'));
    } finally {
      setIsLoadingTones(false);
    }
  }, []);

  // Sayfa açıldığında tonları yükle
  useEffect(() => {
    loadTones();
  }, [loadTones]);

  const generateText = async (formData: ListingFormData) => {
    setIsGenerating(true);
    setError(null);
    try {
      const response = await listingsApi.generateListingText(formData);
      setResult(response);
      return response;
    } catch (err) {
      console.error("İlan metni üretim hatası:", err);
      setError(getErrorMessage(err, 'generate'));
      return null;
    } finally {
      setIsGenerating(false);
    }
  };

  const regenerateText = async (formData: ListingFormData) => {
    setIsGenerating(true);
    setError(null);
    try {
      const response = await listingsApi.regenerateText(formData);
      setResult(response);
      return response;
    } catch (err) {
      console.error("İlan metni yeniden üretim hatası:", err);
      setError(getErrorMessage(err, 'regenerate'));
      return null;
    } finally {
      setIsGenerating(false);
    }
  };

  return {
    isGenerating,
    isLoadingTones,
    result,
    error,
    tones,
    generateText,
    regenerateText,
    loadTones,
  };
}
