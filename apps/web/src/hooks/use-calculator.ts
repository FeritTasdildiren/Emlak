"use client";

import { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

// ─── Types ──────────────────────────────────────────────────────

/** Backend BankRate yanıtı — GET /api/v1/calculator/rates */
interface ApiBankRate {
  bank_name: string;
  annual_rate: number;
  min_term: number;
  max_term: number;
  min_amount: number;
  max_amount: number;
  updated_at: string;
}

interface ApiBankRatesResponse {
  rates: ApiBankRate[];
  source: string;
  last_updated: string;
}

/** Frontend BankRate tipi — consumer'lar bu tipi kullanır */
export interface BankRate {
  id: string;
  name: string;
  annual_rate: number;
  monthly_rate: number;
  min_term: number;
  max_term: number;
  min_amount: number;
  max_amount: number | null;
  logo_url?: string;
}

export interface CalculatorInput {
  propertyPrice: number;
  downPaymentPercent: number;
  termMonths: number;
}

export interface AmortizationRow {
  month: number;
  payment: number;
  principal: number;
  interest: number;
  remainingBalance: number;
}

export interface BankResult {
  bank: BankRate;
  monthlyPayment: number;
  totalPayment: number;
  totalInterest: number;
  isBestRate: boolean;
}

export interface CalculatorResult {
  loanAmount: number;
  downPayment: number;
  monthlyPayment: number;
  totalPayment: number;
  totalInterest: number;
  principalRatio: number;
  interestRatio: number;
  amortization: AmortizationRow[];
  bankComparisons: BankResult[];
}

// ─── API → Frontend Mapping ─────────────────────────────────────

function mapApiBankRate(rate: ApiBankRate): BankRate {
  // Backend yıllık oran veriyor, aylık oranı hesapla
  const monthlyRate = rate.annual_rate / 12;
  return {
    id: rate.bank_name.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, ""),
    name: rate.bank_name,
    annual_rate: Number(rate.annual_rate),
    monthly_rate: Number(monthlyRate.toFixed(4)),
    min_term: rate.min_term,
    max_term: rate.max_term,
    min_amount: Number(rate.min_amount),
    max_amount: rate.max_amount ? Number(rate.max_amount) : null,
  };
}

// ─── React Query Keys ───────────────────────────────────────────

export const calculatorKeys = {
  all: ["calculator"] as const,
  rates: () => [...calculatorKeys.all, "rates"] as const,
};

// ─── Calculator Logic ───────────────────────────────────────────

/**
 * Standart annuity formülü ile aylık ödeme hesaplama:
 * M = P * [r(1+r)^n] / [(1+r)^n - 1]
 */
function calculateMonthlyPayment(
  principal: number,
  monthlyRate: number,
  termMonths: number
): number {
  if (monthlyRate === 0) return principal / termMonths;
  const r = monthlyRate / 100; // yüzdeyi ondalığa çevir
  const factor = Math.pow(1 + r, termMonths);
  return principal * (r * factor) / (factor - 1);
}

function buildAmortizationTable(
  principal: number,
  monthlyRate: number,
  termMonths: number,
  monthlyPayment: number
): AmortizationRow[] {
  const rows: AmortizationRow[] = [];
  let balance = principal;
  const r = monthlyRate / 100;

  for (let month = 1; month <= termMonths; month++) {
    const interestPortion = balance * r;
    const principalPortion = monthlyPayment - interestPortion;
    balance = Math.max(0, balance - principalPortion);

    rows.push({
      month,
      payment: monthlyPayment,
      principal: principalPortion,
      interest: interestPortion,
      remainingBalance: balance,
    });
  }

  return rows;
}

// ─── Hook ───────────────────────────────────────────────────────

export function useCalculator() {
  const [input, setInput] = useState<CalculatorInput>({
    propertyPrice: 5_000_000,
    downPaymentPercent: 30,
    termMonths: 120,
  });

  const [result, setResult] = useState<CalculatorResult | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);

  // Banka oranlarını API'den çek (staleTime: 30dk — oranlar sık değişmez)
  const {
    data: bankRates,
    isLoading: isLoadingRates,
    error: ratesError,
  } = useQuery({
    queryKey: calculatorKeys.rates(),
    queryFn: async () => {
      const response = await api.get<ApiBankRatesResponse>("/calculator/rates");
      return response.rates.map(mapApiBankRate);
    },
    staleTime: 30 * 60 * 1000, // 30 dakika
    gcTime: 60 * 60 * 1000,    // 60 dakika (gcTime >= staleTime)
  });

  const updateInput = useCallback(
    (partial: Partial<CalculatorInput>) => {
      setInput((prev) => ({ ...prev, ...partial }));
    },
    []
  );

  const calculate = useCallback(() => {
    if (!bankRates || bankRates.length === 0) return;

    setIsCalculating(true);

    // UX için kısa hesaplama gecikmesi
    setTimeout(() => {
      const { propertyPrice, downPaymentPercent, termMonths } = input;
      const downPayment = propertyPrice * (downPaymentPercent / 100);
      const loanAmount = propertyPrice - downPayment;

      // En düşük faizli bankayı birincil hesaplama için kullan
      const primaryBank = bankRates[0];
      const monthlyPayment = calculateMonthlyPayment(
        loanAmount,
        primaryBank.monthly_rate,
        termMonths
      );
      const totalPayment = monthlyPayment * termMonths;
      const totalInterest = totalPayment - loanAmount;
      const principalRatio = (loanAmount / totalPayment) * 100;
      const interestRatio = (totalInterest / totalPayment) * 100;

      const amortization = buildAmortizationTable(
        loanAmount,
        primaryBank.monthly_rate,
        termMonths,
        monthlyPayment
      );

      // Banka karşılaştırmaları
      const bankResults: BankResult[] = bankRates.map((bank) => {
        const mp = calculateMonthlyPayment(
          loanAmount,
          bank.monthly_rate,
          termMonths
        );
        const tp = mp * termMonths;
        const ti = tp - loanAmount;
        return {
          bank,
          monthlyPayment: mp,
          totalPayment: tp,
          totalInterest: ti,
          isBestRate: false,
        };
      });

      // En iyi oranı işaretle
      if (bankResults.length > 0) {
        const bestIdx = bankResults.reduce(
          (minIdx, curr, idx, arr) =>
            curr.monthlyPayment < arr[minIdx].monthlyPayment ? idx : minIdx,
          0
        );
        bankResults[bestIdx].isBestRate = true;
      }

      setResult({
        loanAmount,
        downPayment,
        monthlyPayment,
        totalPayment,
        totalInterest,
        principalRatio,
        interestRatio,
        amortization,
        bankComparisons: bankResults,
      });

      setIsCalculating(false);
    }, 400);
  }, [input, bankRates]);

  const reset = useCallback(() => {
    setResult(null);
    setInput({
      propertyPrice: 5_000_000,
      downPaymentPercent: 30,
      termMonths: 120,
    });
  }, []);

  return {
    input,
    updateInput,
    result,
    isCalculating,
    isLoadingRates,
    ratesError,
    calculate,
    reset,
  };
}
