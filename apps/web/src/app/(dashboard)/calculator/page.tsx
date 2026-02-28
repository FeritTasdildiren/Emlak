"use client";

import { useState } from "react";
import {
  Calculator,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  Building,
  BadgeTurkishLira,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { NumberInput } from "@/components/ui/number-input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { cn, formatCurrency } from "@/lib/utils";
import {
  useCalculator,
  type CalculatorResult,
  type AmortizationRow,
  type BankResult,
} from "@/hooks/use-calculator";

// ─── Term Options ───────────────────────────────────────────────

const TERM_OPTIONS = [
  { value: "60", label: "60 Ay (5 Yıl)" },
  { value: "120", label: "120 Ay (10 Yıl)" },
  { value: "180", label: "180 Ay (15 Yıl)" },
  { value: "240", label: "240 Ay (20 Yıl)" },
  { value: "360", label: "360 Ay (30 Yıl)" },
];

// ─── Donut Chart (SVG) ─────────────────────────────────────────

function DonutChart({
  principalRatio,
  interestRatio,
}: {
  principalRatio: number;
  interestRatio: number;
}) {
  const size = 160;
  const strokeWidth = 24;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const principalDash = (principalRatio / 100) * circumference;
  const interestDash = (interestRatio / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-3">
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="transform -rotate-90"
      >
        {/* Principal arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#ea580c"
          strokeWidth={strokeWidth}
          strokeDasharray={`${principalDash} ${circumference - principalDash}`}
          strokeDashoffset="0"
          strokeLinecap="round"
        />
        {/* Interest arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#94a3b8"
          strokeWidth={strokeWidth}
          strokeDasharray={`${interestDash} ${circumference - interestDash}`}
          strokeDashoffset={`${-principalDash}`}
          strokeLinecap="round"
        />
      </svg>
      <div className="flex items-center gap-4 text-sm">
        <div className="flex items-center gap-1.5">
          <div className="h-3 w-3 rounded-full bg-orange-600" />
          <span className="text-gray-600">
            Anapara %{principalRatio.toFixed(0)}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-3 w-3 rounded-full bg-slate-400" />
          <span className="text-gray-600">
            Faiz %{interestRatio.toFixed(0)}
          </span>
        </div>
      </div>
    </div>
  );
}

// ─── Loading Skeleton ───────────────────────────────────────────

function ResultSkeleton() {
  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="p-6 space-y-4">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-12 w-48" />
          <div className="grid grid-cols-3 gap-3">
            <Skeleton className="h-20 rounded-lg" />
            <Skeleton className="h-20 rounded-lg" />
            <Skeleton className="h-20 rounded-lg" />
          </div>
          <Skeleton className="h-40 w-40 rounded-full mx-auto" />
        </CardContent>
      </Card>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Skeleton key={i} className="h-32 rounded-lg" />
        ))}
      </div>
    </div>
  );
}

// ─── Result Summary ─────────────────────────────────────────────

function ResultSummary({ result }: { result: CalculatorResult }) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
          {/* Numbers */}
          <div className="space-y-5">
            <div>
              <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">
                Aylık Taksit
              </p>
              <p className="text-4xl font-bold text-orange-600 mt-1">
                {formatCurrency(result.monthlyPayment)}
              </p>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-lg bg-gray-50 p-3 text-center">
                <p className="text-xs text-gray-500 mb-1">Kredi Tutarı</p>
                <p className="text-sm font-semibold text-gray-900">
                  {formatCurrency(result.loanAmount)}
                </p>
              </div>
              <div className="rounded-lg bg-gray-50 p-3 text-center">
                <p className="text-xs text-gray-500 mb-1">Toplam Ödeme</p>
                <p className="text-sm font-semibold text-gray-900">
                  {formatCurrency(result.totalPayment)}
                </p>
              </div>
              <div className="rounded-lg bg-gray-50 p-3 text-center">
                <p className="text-xs text-gray-500 mb-1">Toplam Faiz</p>
                <p className="text-sm font-semibold text-gray-900">
                  {formatCurrency(result.totalInterest)}
                </p>
              </div>
            </div>
          </div>

          {/* Donut chart */}
          <div className="flex justify-center">
            <DonutChart
              principalRatio={result.principalRatio}
              interestRatio={result.interestRatio}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Amortization Table ─────────────────────────────────────────

function AmortizationTable({ rows }: { rows: AmortizationRow[] }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const displayRows = isExpanded ? rows : rows.slice(0, 12);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Amortisman Tablosu</CardTitle>
          <Badge variant="secondary">{rows.length} Ay</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="py-2 pr-3 font-medium text-gray-500">Ay</th>
                <th className="py-2 pr-3 font-medium text-gray-500 text-right">
                  Taksit
                </th>
                <th className="py-2 pr-3 font-medium text-gray-500 text-right">
                  Anapara
                </th>
                <th className="py-2 pr-3 font-medium text-gray-500 text-right">
                  Faiz
                </th>
                <th className="py-2 font-medium text-gray-500 text-right">
                  Kalan Borç
                </th>
              </tr>
            </thead>
            <tbody>
              {displayRows.map((row) => (
                <tr
                  key={row.month}
                  className="border-b last:border-0 hover:bg-gray-50"
                >
                  <td className="py-2 pr-3 font-medium text-gray-900">
                    {row.month}
                  </td>
                  <td className="py-2 pr-3 text-right text-gray-700">
                    {formatCurrency(row.payment)}
                  </td>
                  <td className="py-2 pr-3 text-right text-orange-600 font-medium">
                    {formatCurrency(row.principal)}
                  </td>
                  <td className="py-2 pr-3 text-right text-gray-500">
                    {formatCurrency(row.interest)}
                  </td>
                  <td className="py-2 text-right text-gray-700">
                    {formatCurrency(row.remainingBalance)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {rows.length > 12 && (
          <div className="mt-4 text-center">
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="h-4 w-4" />
                  Daralt
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4" />
                  Tümünü Göster ({rows.length} Ay)
                </>
              )}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ─── Bank Comparison Card ───────────────────────────────────────

function BankComparisonCard({ bankResult }: { bankResult: BankResult }) {
  const { bank, monthlyPayment, totalPayment, isBestRate } = bankResult;

  return (
    <Card
      className={cn(
        "transition-all",
        isBestRate
          ? "border-green-500 ring-1 ring-green-500 bg-green-50/30"
          : "hover:shadow-md"
      )}
    >
      <CardContent className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-10 w-10 rounded-lg bg-gray-100 flex items-center justify-center">
              <Building className="h-5 w-5 text-gray-500" />
            </div>
            <div>
              <p className="font-semibold text-gray-900 text-sm">
                {bank.name}
              </p>
              <p className="text-xs text-gray-500">
                %{bank.monthly_rate.toFixed(2)} aylık
              </p>
            </div>
          </div>
          {isBestRate && (
            <Badge variant="success" className="text-xs">
              En Uygun
            </Badge>
          )}
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-lg bg-gray-50 p-2 text-center">
            <p className="text-xs text-gray-500">Aylık Taksit</p>
            <p className="text-sm font-bold text-gray-900">
              {formatCurrency(monthlyPayment)}
            </p>
          </div>
          <div className="rounded-lg bg-gray-50 p-2 text-center">
            <p className="text-xs text-gray-500">Toplam Ödeme</p>
            <p className="text-sm font-bold text-gray-900">
              {formatCurrency(totalPayment)}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Bank Comparisons Section ───────────────────────────────────

function BankComparisons({
  bankResults,
}: {
  bankResults: BankResult[];
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <TrendingUp className="h-5 w-5 text-orange-600" />
        <h3 className="text-lg font-semibold text-gray-900">
          Banka Karşılaştırma
        </h3>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {bankResults.map((br) => (
          <BankComparisonCard key={br.bank.id} bankResult={br} />
        ))}
      </div>
    </div>
  );
}

// ─── Calculator Form ────────────────────────────────────────────

function CalculatorForm({
  input,
  updateInput,
  onCalculate,
  isCalculating,
}: {
  input: { propertyPrice: number; downPaymentPercent: number; termMonths: number };
  updateInput: (partial: Partial<typeof input>) => void;
  onCalculate: () => void;
  isCalculating: boolean;
}) {
  const downPaymentAmount = input.propertyPrice * (input.downPaymentPercent / 100);
  const loanAmount = input.propertyPrice - downPaymentAmount;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <BadgeTurkishLira className="h-5 w-5 text-orange-600" />
          Kredi Bilgileri
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Property Price */}
        <NumberInput
          label="Emlak Fiyatı"
          value={input.propertyPrice}
          onChange={(val) => updateInput({ propertyPrice: val ?? 0 })}
          min={100_000}
          step={100_000}
          suffix="₺"
        />

        {/* Down Payment */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">
            Peşinat Oranı
          </label>
          <div className="flex items-center gap-3">
            <input
              type="range"
              min={10}
              max={90}
              step={5}
              value={input.downPaymentPercent}
              onChange={(e) =>
                updateInput({ downPaymentPercent: Number(e.target.value) })
              }
              className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-orange-600"
            />
            <span className="text-sm font-semibold text-gray-900 w-12 text-right">
              %{input.downPaymentPercent}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Peşinat: {formatCurrency(downPaymentAmount)}</span>
            <span>Kredi: {formatCurrency(loanAmount)}</span>
          </div>
        </div>

        {/* Term */}
        <Select
          label="Vade"
          options={TERM_OPTIONS}
          value={String(input.termMonths)}
          onChange={(e) => updateInput({ termMonths: Number(e.target.value) })}
        />

        {/* Calculate Button */}
        <Button
          fullWidth
          className="bg-orange-600 hover:bg-orange-700 text-white gap-2 mt-2"
          onClick={onCalculate}
          loading={isCalculating}
          disabled={isCalculating || input.propertyPrice < 100_000}
        >
          <Calculator className="h-4 w-4" />
          Hesapla
        </Button>
      </CardContent>
    </Card>
  );
}

// ─── Empty State ────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-200 bg-gray-50/50 px-6 py-16 text-center">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-orange-100">
        <Calculator className="h-7 w-7 text-orange-600" />
      </div>
      <h3 className="mt-4 text-lg font-semibold text-gray-900">
        Kredi Hesaplaması Yapın
      </h3>
      <p className="mt-2 max-w-sm text-sm text-gray-500">
        Soldaki formu doldurup &quot;Hesapla&quot; butonuna tıklayarak detaylı
        kredi hesaplaması, amortisman tablosu ve banka karşılaştırması
        yapabilirsiniz.
      </p>
    </div>
  );
}

// ─── Main Page ──────────────────────────────────────────────────

export default function CalculatorPage() {
  const { input, updateInput, result, isCalculating, calculate } =
    useCalculator();

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2">
          <Calculator className="h-6 w-6 text-orange-600" />
          <h1 className="text-2xl font-bold text-gray-900">
            Kredi Hesaplayıcı
          </h1>
        </div>
        <p className="mt-1 text-gray-500">
          Emlak kredisi hesaplama, amortisman tablosu ve banka faiz oranları
          karşılaştırması.
        </p>
      </div>

      {/* Layout: Form + Results */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Form Panel */}
        <div className="lg:col-span-4">
          <div className="lg:sticky lg:top-4">
            <CalculatorForm
              input={input}
              updateInput={updateInput}
              onCalculate={calculate}
              isCalculating={isCalculating}
            />
          </div>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-8 space-y-6">
          {isCalculating ? (
            <ResultSkeleton />
          ) : result ? (
            <>
              <ResultSummary result={result} />
              <BankComparisons bankResults={result.bankComparisons} />
              <AmortizationTable rows={result.amortization} />
            </>
          ) : (
            <EmptyState />
          )}
        </div>
      </div>
    </div>
  );
}
