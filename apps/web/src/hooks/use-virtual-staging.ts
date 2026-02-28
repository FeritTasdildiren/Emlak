import { useState, useEffect, useCallback } from 'react';
import { StagingRequest, StagingResponse, StyleInfo, RoomAnalysis } from '@/types/listing';
import { listingsApi } from '@/lib/api/listings';

export function useVirtualStaging() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<StagingResponse | null>(null);
  const [roomAnalysis, setRoomAnalysis] = useState<RoomAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [styles, setStyles] = useState<StyleInfo[]>([]);
  const [isLoadingStyles, setIsLoadingStyles] = useState(false);

  const loadStyles = useCallback(async () => {
    setIsLoadingStyles(true);
    try {
      const data = await listingsApi.getStagingStyles();
      setStyles(data);
    } catch (err) {
      console.error("Tarzlar yüklenirken hata oluştu:", err);
      setError('Tarz listesi yüklenemedi. Lütfen sayfayı yenileyin.');
    } finally {
      setIsLoadingStyles(false);
    }
  }, []);

  // Sayfa açıldığında tarzları yükle
  useEffect(() => {
    loadStyles();
  }, [loadStyles]);

  const stageImage = async (request: StagingRequest) => {
    setIsProcessing(true);
    setError(null);
    try {
      const response = await listingsApi.virtualStage(request);
      setResult(response);
      return response;
    } catch (err) {
      console.error("Virtual staging hatası:", err);
      const message = err instanceof Error ? err.message : '';
      if (message.includes('kota')) {
        setError('Aylık sahneleme kotanız doldu. Plan yükseltmesi yapabilirsiniz.');
      } else if (message.includes('bos') || message.includes('empty')) {
        setError('Oda boş değil gibi görünüyor. Sahneleme yalnızca boş odalar için çalışır.');
      } else {
        setError('Virtual staging işlemi sırasında bir hata oluştu. Lütfen tekrar deneyin.');
      }
      return null;
    } finally {
      setIsProcessing(false);
    }
  };

  const analyzeRoom = async (imageFile: File) => {
    setIsAnalyzing(true);
    setError(null);
    try {
      const analysis = await listingsApi.analyzeRoom(imageFile);
      setRoomAnalysis(analysis);
      return analysis;
    } catch (err) {
      console.error("Oda analizi hatası:", err);
      setError('Oda analizi sırasında bir hata oluştu.');
      return null;
    } finally {
      setIsAnalyzing(false);
    }
  };

  return {
    isProcessing,
    isAnalyzing,
    isLoadingStyles,
    result,
    roomAnalysis,
    error,
    styles,
    stageImage,
    analyzeRoom,
    loadStyles,
  };
}
