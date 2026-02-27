"""CreditCalculatorService unit testleri."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.modules.calculator.calculator_service import CreditCalculatorService

# ---------- Yardimci ----------

D = Decimal  # kisaltma


# ---------- calculate_monthly_payment ----------


class TestCalculateMonthlyPayment:
    """Aylik taksit hesaplama testleri."""

    def test_basic_calculation(self) -> None:
        """Standart bir kredi icin aylik taksit hesaplar."""
        # 1M TL, %3.09, 120 ay
        result = CreditCalculatorService.calculate_monthly_payment(
            principal=D("1000000"),
            annual_rate=D("3.09"),
            months=120,
        )
        # Sonuc pozitif Decimal olmali
        assert isinstance(result, Decimal)
        assert result > D("0")
        # 2 ondalik basamak olmali
        assert result == result.quantize(D("0.01"))

    def test_zero_interest_rate(self) -> None:
        """Faizsiz kredide taksit = anapara / ay."""
        result = CreditCalculatorService.calculate_monthly_payment(
            principal=D("120000"),
            annual_rate=D("0"),
            months=12,
        )
        assert result == D("10000.00")

    def test_zero_interest_rate_with_remainder(self) -> None:
        """Faizsiz kredide tam bolunmeyen tutar dogru yuvarlanir."""
        result = CreditCalculatorService.calculate_monthly_payment(
            principal=D("100000"),
            annual_rate=D("0"),
            months=3,
        )
        assert result == D("33333.33")

    def test_short_term_loan(self) -> None:
        """Kisa vadeli (12 ay) kredi hesabi."""
        result = CreditCalculatorService.calculate_monthly_payment(
            principal=D("500000"),
            annual_rate=D("3.09"),
            months=12,
        )
        assert result > D("42000")
        assert result < D("43000")

    def test_long_term_loan(self) -> None:
        """Uzun vadeli (360 ay) kredi hesabi."""
        result = CreditCalculatorService.calculate_monthly_payment(
            principal=D("5000000"),
            annual_rate=D("3.49"),
            months=360,
        )
        assert result > D("0")
        assert isinstance(result, Decimal)

    def test_known_value(self) -> None:
        """Bilinen deger kontrolu — elle hesaplanmis sonuc."""
        # 100_000 TL, %12, 12 ay → aylik taksit yaklasik 8884.88
        result = CreditCalculatorService.calculate_monthly_payment(
            principal=D("100000"),
            annual_rate=D("12"),
            months=12,
        )
        assert result == D("8884.88")


# ---------- calculate_total_payment ----------


class TestCalculateTotalPayment:
    """Toplam odeme testleri."""

    def test_basic(self) -> None:
        """Aylik * ay = toplam odeme."""
        result = CreditCalculatorService.calculate_total_payment(
            monthly=D("8884.88"),
            months=12,
        )
        assert result == D("106618.56")

    def test_single_month(self) -> None:
        """Tek ay icin toplam = aylik."""
        result = CreditCalculatorService.calculate_total_payment(
            monthly=D("50000.00"),
            months=1,
        )
        assert result == D("50000.00")


# ---------- calculate_total_interest ----------


class TestCalculateTotalInterest:
    """Toplam faiz testleri."""

    def test_basic(self) -> None:
        """Toplam faiz = toplam odeme - anapara."""
        result = CreditCalculatorService.calculate_total_interest(
            total_payment=D("106618.56"),
            principal=D("100000"),
        )
        assert result == D("6618.56")

    def test_zero_interest(self) -> None:
        """Faizsiz kredide toplam faiz = 0."""
        result = CreditCalculatorService.calculate_total_interest(
            total_payment=D("100000.00"),
            principal=D("100000.00"),
        )
        assert result == D("0.00")


# ---------- generate_amortization_table ----------


class TestGenerateAmortizationTable:
    """Amortisman tablosu testleri."""

    def test_table_length(self) -> None:
        """Tablo satir sayisi = vade ay sayisi."""
        table = CreditCalculatorService.generate_amortization_table(
            principal=D("100000"),
            annual_rate=D("12"),
            months=12,
        )
        assert len(table) == 12

    def test_first_row_structure(self) -> None:
        """Ilk satir dogru anahtarlara sahip."""
        table = CreditCalculatorService.generate_amortization_table(
            principal=D("100000"),
            annual_rate=D("12"),
            months=12,
        )
        first = table[0]
        assert first["month"] == 1
        assert "payment" in first
        assert "principal_part" in first
        assert "interest_part" in first
        assert "remaining_balance" in first

    def test_last_row_remaining_is_zero(self) -> None:
        """Son satirdaki kalan borc tam 0 olmali."""
        table = CreditCalculatorService.generate_amortization_table(
            principal=D("100000"),
            annual_rate=D("12"),
            months=12,
        )
        last = table[-1]
        assert last["remaining_balance"] == D("0.00")

    def test_last_row_remaining_is_zero_long_term(self) -> None:
        """Uzun vadeli kredide de son satir kalan = 0."""
        table = CreditCalculatorService.generate_amortization_table(
            principal=D("5000000"),
            annual_rate=D("3.49"),
            months=120,
        )
        assert table[-1]["remaining_balance"] == D("0.00")

    def test_payment_equals_principal_plus_interest(self) -> None:
        """Her satirda: payment = principal_part + interest_part."""
        table = CreditCalculatorService.generate_amortization_table(
            principal=D("100000"),
            annual_rate=D("12"),
            months=12,
        )
        for row in table:
            assert row["payment"] == row["principal_part"] + row["interest_part"]

    def test_remaining_decreases(self) -> None:
        """Kalan borc her ay azalir."""
        table = CreditCalculatorService.generate_amortization_table(
            principal=D("1000000"),
            annual_rate=D("3.09"),
            months=120,
        )
        for i in range(1, len(table)):
            assert table[i]["remaining_balance"] < table[i - 1]["remaining_balance"]

    def test_first_row_interest(self) -> None:
        """Ilk ay faizi = anapara * aylik faiz orani."""
        principal = D("100000")
        annual_rate = D("12")
        table = CreditCalculatorService.generate_amortization_table(
            principal=principal,
            annual_rate=annual_rate,
            months=12,
        )
        expected_interest = (principal * annual_rate / D("12") / D("100")).quantize(
            D("0.01"),
        )
        assert table[0]["interest_part"] == expected_interest

    def test_zero_interest_table(self) -> None:
        """Faizsiz kredi amortisman tablosu."""
        table = CreditCalculatorService.generate_amortization_table(
            principal=D("120000"),
            annual_rate=D("0"),
            months=12,
        )
        for row in table:
            assert row["interest_part"] == D("0.00")
        assert table[-1]["remaining_balance"] == D("0.00")

    def test_total_principal_equals_loan(self) -> None:
        """Tum anapara paylari toplami = kredi tutari."""
        principal = D("100000")
        table = CreditCalculatorService.generate_amortization_table(
            principal=principal,
            annual_rate=D("12"),
            months=12,
        )
        total_principal = sum(row["principal_part"] for row in table)
        assert total_principal == principal

    def test_month_numbers_sequential(self) -> None:
        """Ay numaralari 1'den baslayip sirayla artar."""
        table = CreditCalculatorService.generate_amortization_table(
            principal=D("500000"),
            annual_rate=D("3.09"),
            months=24,
        )
        for i, row in enumerate(table):
            assert row["month"] == i + 1


# ---------- calculate_down_payment ----------


class TestCalculateDownPayment:
    """Pesinat hesaplama testleri."""

    def test_standard_20_percent(self) -> None:
        """%20 pesinat hesabi."""
        result = CreditCalculatorService.calculate_down_payment(
            property_price=D("1000000"),
            down_payment_percent=D("20"),
        )
        assert result["down_payment_amount"] == D("200000.00")
        assert result["loan_amount"] == D("800000.00")

    def test_zero_down_payment(self) -> None:
        """%0 pesinat — kredinin tamami."""
        result = CreditCalculatorService.calculate_down_payment(
            property_price=D("1000000"),
            down_payment_percent=D("0"),
        )
        assert result["down_payment_amount"] == D("0.00")
        assert result["loan_amount"] == D("1000000.00")

    def test_full_down_payment(self) -> None:
        """%100 pesinat — kredi yok."""
        result = CreditCalculatorService.calculate_down_payment(
            property_price=D("1000000"),
            down_payment_percent=D("100"),
        )
        assert result["down_payment_amount"] == D("1000000.00")
        assert result["loan_amount"] == D("0.00")

    def test_sum_equals_price(self) -> None:
        """Pesinat + kredi = konut fiyati."""
        price = D("2500000")
        result = CreditCalculatorService.calculate_down_payment(
            property_price=price,
            down_payment_percent=D("35"),
        )
        assert result["down_payment_amount"] + result["loan_amount"] == price

    def test_fractional_percent(self) -> None:
        """Kesirli yuzde icin dogru hesaplama."""
        result = CreditCalculatorService.calculate_down_payment(
            property_price=D("1000000"),
            down_payment_percent=D("17.5"),
        )
        assert result["down_payment_amount"] == D("175000.00")
        assert result["loan_amount"] == D("825000.00")


# ---------- Schema Validation ----------


class TestSchemaValidation:
    """Pydantic schema dogrulama testleri."""

    def test_valid_request(self) -> None:
        """Gecerli istek olusturulabilir."""
        from src.modules.calculator.calculator_schemas import CreditCalculationRequest

        req = CreditCalculationRequest(
            property_price=D("1000000"),
            annual_interest_rate=D("3.09"),
            term_months=120,
        )
        assert req.down_payment_percent == D("20")

    def test_invalid_price_zero(self) -> None:
        """Fiyat 0 olamaz."""
        from src.modules.calculator.calculator_schemas import CreditCalculationRequest

        with pytest.raises(Exception):  # noqa: B017
            CreditCalculationRequest(
                property_price=D("0"),
                annual_interest_rate=D("3.09"),
                term_months=120,
            )

    def test_invalid_term_exceeds_max(self) -> None:
        """Vade 360'tan buyuk olamaz."""
        from src.modules.calculator.calculator_schemas import CreditCalculationRequest

        with pytest.raises(Exception):  # noqa: B017
            CreditCalculationRequest(
                property_price=D("1000000"),
                annual_interest_rate=D("3.09"),
                term_months=361,
            )


# ---------- Bank Rates ----------


class TestBankRates:
    """Banka faiz oranlari testleri."""

    def test_get_bank_rates_returns_list(self) -> None:
        """get_bank_rates liste dondurur."""
        from src.modules.calculator.bank_rates import get_bank_rates

        rates = get_bank_rates()
        assert isinstance(rates, list)
        assert len(rates) == 6

    def test_bank_rates_have_decimal_values(self) -> None:
        """Tum faiz oranlari Decimal tipinde."""
        from src.modules.calculator.bank_rates import get_bank_rates

        rates = get_bank_rates()
        for rate in rates:
            assert isinstance(rate.annual_rate, Decimal)
            assert isinstance(rate.min_amount, Decimal)
            assert isinstance(rate.max_amount, Decimal)

    def test_bank_rates_returns_copy(self) -> None:
        """get_bank_rates orijinal listeyi degil kopya dondurur."""
        from src.modules.calculator.bank_rates import get_bank_rates

        rates1 = get_bank_rates()
        rates2 = get_bank_rates()
        assert rates1 is not rates2

    def test_ziraat_rate(self) -> None:
        """Ziraat Bankasi orani %3.09."""
        from src.modules.calculator.bank_rates import get_bank_rates

        rates = get_bank_rates()
        ziraat = next(r for r in rates if "Ziraat" in r.bank_name)
        assert ziraat.annual_rate == D("3.09")
        assert ziraat.min_term == 12
        assert ziraat.max_term == 120
