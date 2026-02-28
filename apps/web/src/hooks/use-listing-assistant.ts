import { useState, useEffect, useCallback } from 'react';
import { ListingFormData, ListingTextResponse, ToneInfo } from '@/types/listing';
import { listingsApi } from '@/lib/api/listings';

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
      setError('Ton listesi yüklenemedi. Lütfen sayfayı yenileyin.');
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
      const message = err instanceof Error ? err.message : 'İlan metni oluşturulurken bir hata oluştu.';
      setError(
        message.includes('kota')
          ? 'Aylık ilan metni üretim kotanız doldu. Plan yükseltmesi yapabilirsiniz.'
          : 'İlan metni oluşturulurken bir hata oluştu. Lütfen tekrar deneyin.'
      );
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
      setError('İlan metni yeniden üretilirken bir hata oluştu. Lütfen tekrar deneyin.');
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
