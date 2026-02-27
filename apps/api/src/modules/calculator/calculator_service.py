"""Kredi hesaplayici servis — pure Python, DB bagimliligi yok."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

# 2 ondalik basamaga yuvarlama sabiti
_Q2 = Decimal("0.01")


class CreditCalculatorService:
    """Konut kredisi hesaplama servisi.

    Tum metodlar ``@staticmethod`` — state tutmaz, DB'ye bagimli degildir.
    Tum tutarlar ``Decimal`` ile hesaplanir, ``float`` KULLANILMAZ.
    """

    # ---------- Temel Hesaplamalar ----------

    @staticmethod
    def calculate_monthly_payment(
        principal: Decimal,
        annual_rate: Decimal,
        months: int,
    ) -> Decimal:
        """Aylik taksit tutarini hesaplar.

        Formul: M = P * [r(1+r)^n] / [(1+r)^n - 1]
        r = aylik faiz orani = annual_rate / 12 / 100
        n = vade (ay)

        Args:
            principal: Kredi tutari (TL).
            annual_rate: Yillik faiz orani (ör. 3.09 = %3.09).
            months: Vade suresi (ay).

        Returns:
            Aylik taksit tutari, 2 ondalik basamaga yuvarlanmis.
        """
        # Ozel durum: faizsiz kredi
        if annual_rate == Decimal("0"):
            return (principal / months).quantize(_Q2, rounding=ROUND_HALF_UP)

        # Aylik faiz orani
        monthly_rate = annual_rate / Decimal("12") / Decimal("100")

        # (1 + r) ^ n
        compound = (Decimal("1") + monthly_rate) ** months

        # M = P * [r * compound] / [compound - 1]
        payment = principal * (monthly_rate * compound) / (compound - Decimal("1"))

        return payment.quantize(_Q2, rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_total_payment(monthly: Decimal, months: int) -> Decimal:
        """Toplam odeme tutarini hesaplar.

        Args:
            monthly: Aylik taksit tutari (TL).
            months: Vade suresi (ay).

        Returns:
            Toplam odeme tutari, 2 ondalik basamaga yuvarlanmis.
        """
        return (monthly * months).quantize(_Q2, rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_total_interest(
        total_payment: Decimal,
        principal: Decimal,
    ) -> Decimal:
        """Toplam faiz tutarini hesaplar.

        Args:
            total_payment: Toplam odeme tutari (TL).
            principal: Kredi tutari / anapara (TL).

        Returns:
            Toplam faiz tutari, 2 ondalik basamaga yuvarlanmis.
        """
        return (total_payment - principal).quantize(_Q2, rounding=ROUND_HALF_UP)

    # ---------- Amortisman Tablosu ----------

    @staticmethod
    def generate_amortization_table(
        principal: Decimal,
        annual_rate: Decimal,
        months: int,
    ) -> list[dict]:
        """Amortisman tablosu uretir.

        Her satir: month, payment, principal_part, interest_part, remaining_balance.
        Son taksitte yuvarlama farki duzeltilir — remaining_balance tam 0 olur.

        Args:
            principal: Kredi tutari (TL).
            annual_rate: Yillik faiz orani (ör. 3.09 = %3.09).
            months: Vade suresi (ay).

        Returns:
            Amortisman tablosu satirlari.
        """
        monthly_payment = CreditCalculatorService.calculate_monthly_payment(
            principal,
            annual_rate,
            months,
        )

        # Faizsiz kredi icin aylik oran 0
        if annual_rate == Decimal("0"):
            monthly_rate = Decimal("0")
        else:
            monthly_rate = annual_rate / Decimal("12") / Decimal("100")

        table: list[dict] = []
        remaining = principal

        for month_no in range(1, months + 1):
            interest_part = (remaining * monthly_rate).quantize(
                _Q2,
                rounding=ROUND_HALF_UP,
            )

            is_last_month = month_no == months

            if is_last_month:
                # Son taksitte kalan borcun tamami kapatilir
                principal_part = remaining
                payment = (principal_part + interest_part).quantize(
                    _Q2,
                    rounding=ROUND_HALF_UP,
                )
                remaining = Decimal("0.00")
            else:
                principal_part = (monthly_payment - interest_part).quantize(
                    _Q2,
                    rounding=ROUND_HALF_UP,
                )
                remaining = (remaining - principal_part).quantize(
                    _Q2,
                    rounding=ROUND_HALF_UP,
                )
                payment = monthly_payment

            table.append(
                {
                    "month": month_no,
                    "payment": payment,
                    "principal_part": principal_part,
                    "interest_part": interest_part,
                    "remaining_balance": remaining,
                }
            )

        return table

    # ---------- Pesinat ----------

    @staticmethod
    def calculate_down_payment(
        property_price: Decimal,
        down_payment_percent: Decimal,
    ) -> dict:
        """Pesinat ve kredi tutarini hesaplar.

        Args:
            property_price: Konut fiyati (TL).
            down_payment_percent: Pesinat yuzdesi (ör. 20 = %20).

        Returns:
            dict: down_payment_amount ve loan_amount anahtarli sozluk.
        """
        down_payment_amount = (property_price * down_payment_percent / Decimal("100")).quantize(
            _Q2, rounding=ROUND_HALF_UP
        )

        loan_amount = (property_price - down_payment_amount).quantize(
            _Q2,
            rounding=ROUND_HALF_UP,
        )

        return {
            "down_payment_amount": down_payment_amount,
            "loan_amount": loan_amount,
        }
