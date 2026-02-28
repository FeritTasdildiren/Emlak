import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useCalculator } from "../use-calculator";

describe("useCalculator", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  // ─── Varsayılan Değerler ────────────────────────────────────

  it("varsayılan input değerleriyle başlar", () => {
    const { result } = renderHook(() => useCalculator());

    expect(result.current.input).toEqual({
      propertyPrice: 5_000_000,
      downPaymentPercent: 30,
      termMonths: 120,
    });
    expect(result.current.result).toBeNull();
    expect(result.current.isCalculating).toBe(false);
  });

  // ─── Input Güncelleme ──────────────────────────────────────

  it("updateInput ile propertyPrice güncellenir", () => {
    const { result } = renderHook(() => useCalculator());

    act(() => {
      result.current.updateInput({ propertyPrice: 3_000_000 });
    });

    expect(result.current.input.propertyPrice).toBe(3_000_000);
    // Diğer değerler korunmalı
    expect(result.current.input.downPaymentPercent).toBe(30);
    expect(result.current.input.termMonths).toBe(120);
  });

  it("updateInput ile birden fazla alan güncellenir", () => {
    const { result } = renderHook(() => useCalculator());

    act(() => {
      result.current.updateInput({
        propertyPrice: 10_000_000,
        downPaymentPercent: 50,
      });
    });

    expect(result.current.input.propertyPrice).toBe(10_000_000);
    expect(result.current.input.downPaymentPercent).toBe(50);
  });

  // ─── Hesaplama (calculate) ─────────────────────────────────

  it("calculate çağrıldığında isCalculating true olur", () => {
    const { result } = renderHook(() => useCalculator());

    act(() => {
      result.current.calculate();
    });

    expect(result.current.isCalculating).toBe(true);
  });

  it("calculate sonrası doğru kredi tutarı hesaplar", () => {
    const { result } = renderHook(() => useCalculator());

    act(() => {
      result.current.calculate();
    });

    // setTimeout tamamlansın (400ms)
    act(() => {
      vi.advanceTimersByTime(400);
    });

    expect(result.current.isCalculating).toBe(false);
    expect(result.current.result).not.toBeNull();

    // 5M * %30 peşinat = 1.5M peşinat, 3.5M kredi
    expect(result.current.result!.downPayment).toBe(1_500_000);
    expect(result.current.result!.loanAmount).toBe(3_500_000);
  });

  it("aylık ödeme kredi tutarından büyük olmalı (faiz dahil)", () => {
    const { result } = renderHook(() => useCalculator());

    act(() => {
      result.current.calculate();
    });
    act(() => {
      vi.advanceTimersByTime(400);
    });

    const { monthlyPayment, loanAmount, totalPayment } = result.current.result!;

    // Aylık ödeme pozitif olmalı
    expect(monthlyPayment).toBeGreaterThan(0);
    // Toplam ödeme kredi tutarından büyük olmalı (faiz nedeniyle)
    expect(totalPayment).toBeGreaterThan(loanAmount);
  });

  it("principalRatio + interestRatio toplamı ~100 olmalı", () => {
    const { result } = renderHook(() => useCalculator());

    act(() => {
      result.current.calculate();
    });
    act(() => {
      vi.advanceTimersByTime(400);
    });

    const { principalRatio, interestRatio } = result.current.result!;
    expect(principalRatio + interestRatio).toBeCloseTo(100, 1);
  });

  // ─── Amortisman Tablosu ────────────────────────────────────

  it("amortisman tablosu doğru sayıda satır içerir", () => {
    const { result } = renderHook(() => useCalculator());

    act(() => {
      result.current.updateInput({ termMonths: 24 });
    });
    act(() => {
      result.current.calculate();
    });
    act(() => {
      vi.advanceTimersByTime(400);
    });

    expect(result.current.result!.amortization).toHaveLength(24);
  });

  it("amortisman tablosunun son satırında kalan bakiye ~0 olmalı", () => {
    const { result } = renderHook(() => useCalculator());

    act(() => {
      result.current.calculate();
    });
    act(() => {
      vi.advanceTimersByTime(400);
    });

    const amortization = result.current.result!.amortization;
    const lastRow = amortization[amortization.length - 1];
    expect(lastRow.remainingBalance).toBeCloseTo(0, 0);
  });

  it("amortisman tablosunda her satırda anapara + faiz = ödeme", () => {
    const { result } = renderHook(() => useCalculator());

    act(() => {
      result.current.calculate();
    });
    act(() => {
      vi.advanceTimersByTime(400);
    });

    const amortization = result.current.result!.amortization;
    for (const row of amortization) {
      expect(row.principal + row.interest).toBeCloseTo(row.payment, 2);
    }
  });

  // ─── Banka Karşılaştırması ─────────────────────────────────

  it("banka karşılaştırmasında en az bir isBestRate=true olmalı", () => {
    const { result } = renderHook(() => useCalculator());

    act(() => {
      result.current.calculate();
    });
    act(() => {
      vi.advanceTimersByTime(400);
    });

    const bestBanks = result.current.result!.bankComparisons.filter(
      (b) => b.isBestRate
    );
    expect(bestBanks).toHaveLength(1);
  });

  it("en düşük faizli banka isBestRate olarak işaretlenmeli", () => {
    const { result } = renderHook(() => useCalculator());

    act(() => {
      result.current.calculate();
    });
    act(() => {
      vi.advanceTimersByTime(400);
    });

    const comparisons = result.current.result!.bankComparisons;
    const bestBank = comparisons.find((b) => b.isBestRate)!;
    const minPayment = Math.min(...comparisons.map((b) => b.monthlyPayment));
    expect(bestBank.monthlyPayment).toBe(minPayment);
  });

  // ─── Reset ─────────────────────────────────────────────────

  it("reset fonksiyonu değerleri varsayılana döndürür", () => {
    const { result } = renderHook(() => useCalculator());

    // Değerleri değiştir ve hesapla
    act(() => {
      result.current.updateInput({ propertyPrice: 10_000_000 });
    });
    act(() => {
      result.current.calculate();
    });
    act(() => {
      vi.advanceTimersByTime(400);
    });

    expect(result.current.result).not.toBeNull();

    // Reset
    act(() => {
      result.current.reset();
    });

    expect(result.current.input.propertyPrice).toBe(5_000_000);
    expect(result.current.input.downPaymentPercent).toBe(30);
    expect(result.current.input.termMonths).toBe(120);
    expect(result.current.result).toBeNull();
  });

  // ─── Edge Cases ────────────────────────────────────────────

  it("%0 peşinat ile tüm fiyat kredi olarak hesaplanır", () => {
    const { result } = renderHook(() => useCalculator());

    act(() => {
      result.current.updateInput({ downPaymentPercent: 0 });
    });
    act(() => {
      result.current.calculate();
    });
    act(() => {
      vi.advanceTimersByTime(400);
    });

    expect(result.current.result!.downPayment).toBe(0);
    expect(result.current.result!.loanAmount).toBe(5_000_000);
  });

  it("%100 peşinat ile kredi tutarı 0 olur", () => {
    const { result } = renderHook(() => useCalculator());

    act(() => {
      result.current.updateInput({ downPaymentPercent: 100 });
    });
    act(() => {
      result.current.calculate();
    });
    act(() => {
      vi.advanceTimersByTime(400);
    });

    expect(result.current.result!.loanAmount).toBe(0);
    expect(result.current.result!.monthlyPayment).toBe(0);
  });
});
