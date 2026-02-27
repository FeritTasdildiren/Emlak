"""
Sprint S9 Unit Test Suite — Vitrin + Kredi Hesaplama

Pure unit testleri — DB bagimliligi YOK, mock pattern kullanir.

Test kategorileri:
  1. TestShowcaseSlugGeneration — Turkce karakter normalizasyonu, slug formati (5 test)
  2. TestWhatsAppLinkGeneration — Telefon normalizasyonu, URL formati (4 test)
  3. TestShowcaseSchemas — ShowcaseCreate/Update validasyonu (5 test)
  4. TestAnnuityFormulaVerification — QA-specific exact value kontrolleri (5 test)
  5. TestCalculatorSchemaValidation — CreditCalculationRequest validasyonu (5 test)
  6. TestBankRates — Banka faiz orani veri butunlugu (4 test)

Toplam: 28 test
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.calculator.bank_rates import get_bank_rates
from src.modules.calculator.calculator_schemas import CreditCalculationRequest
from src.modules.calculator.calculator_service import CreditCalculatorService
from src.modules.showcases.schemas import (
    ShowcaseCreate,
    ShowcasePublicResponse,
    ShowcaseUpdate,
)
from src.modules.showcases.service import ShowcaseService

# Decimal kisaltma
D = Decimal


# ================================================================
# 1. TestShowcaseSlugGeneration — Turkce normalizasyon, slug formati
# ================================================================


class TestShowcaseSlugGeneration:
    """S9-TC-001 (P0): Slug olusturma — Turkce karakter normalizasyonu.

    ShowcaseService.generate_slug(), basliktan kebab-case slug uretir.
    Turkce ozel karakterler ASCII karsiliklarina donusturulur.
    """

    @staticmethod
    def _mock_db_no_conflict() -> AsyncMock:
        """Slug cakismasi OLMAYAN mock DB session."""
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 0
        db.execute.return_value = mock_result
        return db

    @pytest.mark.asyncio
    async def test_turkish_chars_normalized(self) -> None:
        """Turkce ozel karakterler (s, c, u, o, i, g) ASCII'ye donusturulur."""
        db = self._mock_db_no_conflict()
        slug = await ShowcaseService.generate_slug(db, "Guzel Koseler")
        # u, o gibi normal ASCII karakterler zaten gecerli
        assert slug == "guzel-koseler"

    @pytest.mark.asyncio
    async def test_turkish_special_chars_scuoig(self) -> None:
        """ş→s, ç→c, ü→u, ö→o, ı→i, ğ→g donusumleri dogru calisir."""
        db = self._mock_db_no_conflict()
        slug = await ShowcaseService.generate_slug(db, "Şişli Çökertme Üğür")
        # s-isli → sisli, c-okertme → cokertme, u-gur → ugur
        assert "s" in slug  # s -> s
        assert "c" in slug  # c -> c
        assert "u" in slug  # u -> u
        assert "ş" not in slug
        assert "ç" not in slug
        assert "ü" not in slug
        assert "ö" not in slug
        assert "ı" not in slug
        assert "ğ" not in slug

    @pytest.mark.asyncio
    async def test_slug_kebab_case_format(self) -> None:
        """Slug kebab-case formatinda olmali (kucuk harf, tire ayirici)."""
        db = self._mock_db_no_conflict()
        slug = await ShowcaseService.generate_slug(db, "Kadıköy Sahil Vitrin")
        # kadikoy-sahil-vitrin
        assert slug == "kadikoy-sahil-vitrin"
        assert " " not in slug
        assert slug == slug.lower()

    @pytest.mark.asyncio
    async def test_slug_conflict_appends_suffix(self) -> None:
        """Cakisma durumunda slug'a rastgele suffix eklenir."""
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 1  # cakisma var
        db.execute.return_value = mock_result

        slug = await ShowcaseService.generate_slug(db, "Test Vitrin")
        # Base slug: test-vitrin, cakisma var → test-vitrin-<6hex>
        assert slug.startswith("test-vitrin-")
        suffix = slug.split("test-vitrin-")[1]
        assert len(suffix) == 6

    @pytest.mark.asyncio
    async def test_empty_title_fallback(self) -> None:
        """Bos veya sadece ozel karakter iceren baslik 'vitrin' fallback slug uretir."""
        db = self._mock_db_no_conflict()
        slug = await ShowcaseService.generate_slug(db, "---")
        assert slug == "vitrin"


# ================================================================
# 2. TestWhatsAppLinkGeneration — Telefon normalizasyonu, URL formati
# ================================================================


class TestWhatsAppLinkGeneration:
    """S9-TC-009 (P1): WhatsApp click-to-chat link olusturma.

    ShowcaseService.generate_whatsapp_link() telefon numarasini normalize eder
    ve WhatsApp click-to-chat URL'i uretir.
    """

    def test_phone_with_plus90_prefix(self) -> None:
        """+90 ile baslayan numara dogru normalize edilir."""
        url = ShowcaseService.generate_whatsapp_link(
            phone="+90 532 123 4567",
            showcase_title="Test Vitrin",
            slug="test-vitrin",
        )
        assert url.startswith("https://wa.me/905321234567")
        assert "text=" in url

    def test_phone_with_zero_prefix(self) -> None:
        """0 ile baslayan numara (05xx) -> 905xx normalize edilir."""
        url = ShowcaseService.generate_whatsapp_link(
            phone="05321234567",
            showcase_title="Guzel Ev",
            slug="guzel-ev",
        )
        assert "wa.me/905321234567" in url

    def test_phone_ten_digits_no_prefix(self) -> None:
        """10 haneli numara (5xx) -> 905xx normalize edilir."""
        url = ShowcaseService.generate_whatsapp_link(
            phone="5321234567",
            showcase_title="Sahil",
            slug="sahil",
        )
        assert "wa.me/905321234567" in url

    def test_invalid_phone_raises(self) -> None:
        """Gecersiz telefon numarasi ValueError firlatir."""
        with pytest.raises(ValueError, match="Gecersiz telefon numarasi"):
            ShowcaseService.generate_whatsapp_link(
                phone="123",
                showcase_title="Test",
                slug="test",
            )


# ================================================================
# 3. TestShowcaseSchemas — ShowcaseCreate/Update validasyonu
# ================================================================


class TestShowcaseSchemas:
    """S9-TC-020 (P1), S9-TC-021 (P0): Showcase schema validasyonu.

    ShowcaseCreate, ShowcaseUpdate, ShowcasePublicResponse dogrulama testleri.
    """

    def test_showcase_create_valid(self) -> None:
        """Gecerli ShowcaseCreate olusturulabilir."""
        sc = ShowcaseCreate(
            title="Kadikoy Sahil Portfoyu",
            selected_properties=["uuid-1", "uuid-2"],
        )
        assert sc.title == "Kadikoy Sahil Portfoyu"
        assert sc.theme == "default"
        assert len(sc.selected_properties) == 2

    def test_showcase_create_title_min_length(self) -> None:
        """ShowcaseCreate title min 2 karakter olmali."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ShowcaseCreate(
                title="A",  # 1 karakter — gecersiz
                selected_properties=["uuid-1"],
            )

    def test_showcase_update_partial_fields(self) -> None:
        """ShowcaseUpdate sadece gonderilen alanlari icerir (partial update)."""
        su = ShowcaseUpdate(title="Yeni Baslik")
        data = su.model_dump(exclude_unset=True)
        assert "title" in data
        assert "description" not in data
        assert "selected_properties" not in data

    def test_showcase_update_is_active_toggle(self) -> None:
        """ShowcaseUpdate ile is_active toggle edilebilir."""
        su = ShowcaseUpdate(is_active=False)
        data = su.model_dump(exclude_unset=True)
        assert data["is_active"] is False

    def test_showcase_public_response_schema(self) -> None:
        """S9-TC-021: ShowcasePublicResponse tum gerekli alanlara sahip."""
        resp = ShowcasePublicResponse(
            slug="kadikoy-sahil",
            title="Kadikoy Sahil Portfoyu",
            description="En iyi sahil ilanlari",
            agent_phone="+905321234567",
            agent_email="agent@test.com",
            agent_whatsapp="+905321234567",
            agent_photo_url=None,
            theme="modern",
            properties=[],
            views_count=42,
        )
        assert resp.slug == "kadikoy-sahil"
        assert resp.views_count == 42
        assert resp.properties == []
        assert resp.theme == "modern"


# ================================================================
# 4. TestAnnuityFormulaVerification — QA exact value kontrolleri
# ================================================================


class TestAnnuityFormulaVerification:
    """S9-TC-012 (P0), S9-TC-013 (P0): Annuity formul dogrulamasi.

    QA dokumanindaki spesifik degerler ile hesaplama dogrulanir.
    Mevcut test_calculator_service.py'de bulunmayan S9-specific senaryolar.
    """

    def test_s9_tc_013_annuity_exact_value(self) -> None:
        """S9-TC-013: 1M TL, %2.0/ay (%24 yillik), 12 ay → ~94,559.61 TL.

        Formul: M = P * [r(1+r)^n] / [(1+r)^n - 1]
        r = 24 / 12 / 100 = 0.02, n = 12
        M = 1_000_000 * [0.02 * 1.02^12] / [1.02^12 - 1]
        """
        monthly = CreditCalculatorService.calculate_monthly_payment(
            principal=D("1000000"),
            annual_rate=D("24"),  # %24 yillik = %2 aylik
            months=12,
        )
        # Beklenen deger: ~94,559.60 veya 94,559.61 (Decimal yuvarlamasina bagli)
        assert abs(monthly - D("94559.60")) < D("0.02")

    def test_s9_tc_012_annuity_formula_mathematical_check(self) -> None:
        """S9-TC-012: Annuity formul dongusel dogrulama.

        Hesaplanan aylik taksit * vade = toplam odeme.
        Toplam odeme - anapara = toplam faiz.
        Amortisman tablosundaki toplam = bu degerlere esit olmali.
        """
        principal = D("1000000")
        annual_rate = D("24")
        months = 12

        monthly = CreditCalculatorService.calculate_monthly_payment(principal, annual_rate, months)
        total = CreditCalculatorService.calculate_total_payment(monthly, months)
        interest = CreditCalculatorService.calculate_total_interest(total, principal)

        # Toplam odeme > anapara (faiz var)
        assert total > principal
        # Faiz = toplam - anapara
        assert interest == total - principal
        # Faiz pozitif
        assert interest > D("0")

    def test_s9_tc_016_zero_interest_specific(self) -> None:
        """S9-TC-016: Faizsiz kredi — aylik taksit = anapara / vade.

        S9 spesifik senaryo: 1M TL, %0 faiz, 12 ay.
        """
        monthly = CreditCalculatorService.calculate_monthly_payment(
            principal=D("1000000"),
            annual_rate=D("0"),
            months=12,
        )
        assert monthly == D("83333.33")

        total = CreditCalculatorService.calculate_total_payment(monthly, 12)
        interest = CreditCalculatorService.calculate_total_interest(total, D("1000000"))
        # Faizsiz: toplam faiz ~0 (yuvarlama farki olabilir)
        assert abs(interest) < D("1.00")

    def test_s9_tc_015_multiple_scenario_comparison(self) -> None:
        """S9-TC-015: Farkli faiz oranlariyla karsilastirma.

        Dusuk faiz → dusuk taksit. 3 farkli oranda siralamanin korunmasi.
        """
        rates = [D("3.09"), D("3.29"), D("3.49")]
        payments = []
        for rate in rates:
            m = CreditCalculatorService.calculate_monthly_payment(
                principal=D("1000000"),
                annual_rate=rate,
                months=120,
            )
            payments.append(m)

        # Dusuk faiz → dusuk taksit
        assert payments[0] < payments[1] < payments[2]

    def test_s9_tc_022_full_calculation_pipeline(self) -> None:
        """S9-TC-022: Tam hesaplama pipeline — pesinat, aylik taksit, amortisman.

        Konut fiyati 5M, %20 pesinat, %3.09, 120 ay.
        """
        # Pesinat
        dp = CreditCalculatorService.calculate_down_payment(
            property_price=D("5000000"),
            down_payment_percent=D("20"),
        )
        assert dp["down_payment_amount"] == D("1000000.00")
        assert dp["loan_amount"] == D("4000000.00")

        # Aylik taksit
        monthly = CreditCalculatorService.calculate_monthly_payment(
            principal=dp["loan_amount"],
            annual_rate=D("3.09"),
            months=120,
        )
        assert monthly > D("0")
        assert isinstance(monthly, Decimal)

        # Amortisman tablosu
        table = CreditCalculatorService.generate_amortization_table(
            principal=dp["loan_amount"],
            annual_rate=D("3.09"),
            months=120,
        )
        assert len(table) == 120
        assert table[-1]["remaining_balance"] == D("0.00")


# ================================================================
# 5. TestCalculatorSchemaValidation — CreditCalculationRequest
# ================================================================


class TestCalculatorSchemaValidation:
    """S9-TC-017 (P2), S9-TC-018 (P2): Hesaplayici schema validasyonu.

    CreditCalculationRequest field kısıtlamalari test edilir.
    Mevcut testlerden farkli: negatif tutar ve sifir vade senaryolari.
    """

    def test_s9_tc_017_negative_amount_rejected(self) -> None:
        """S9-TC-017: Negatif konut fiyati reddedilmeli."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CreditCalculationRequest(
                property_price=D("-500000"),
                annual_interest_rate=D("3.09"),
                term_months=120,
            )

    def test_s9_tc_018_zero_term_rejected(self) -> None:
        """S9-TC-018: Sifir vade suresi reddedilmeli (gt=0)."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CreditCalculationRequest(
                property_price=D("1000000"),
                annual_interest_rate=D("3.09"),
                term_months=0,
            )

    def test_down_payment_over_100_rejected(self) -> None:
        """Pesinat yuzdesi %100'u asamaz."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CreditCalculationRequest(
                property_price=D("1000000"),
                annual_interest_rate=D("3.09"),
                term_months=120,
                down_payment_percent=D("101"),
            )

    def test_annual_rate_zero_rejected(self) -> None:
        """Yillik faiz orani 0 olamaz (gt=0 constrainti)."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CreditCalculationRequest(
                property_price=D("1000000"),
                annual_interest_rate=D("0"),
                term_months=120,
            )

    def test_valid_request_defaults(self) -> None:
        """Gecerli istek default degerleri dogru atar."""
        req = CreditCalculationRequest(
            property_price=D("2000000"),
            annual_interest_rate=D("3.49"),
            term_months=60,
        )
        assert req.down_payment_percent == D("20")
        assert req.term_months == 60


# ================================================================
# 6. TestBankRates — Banka faiz orani veri butunlugu
# ================================================================


class TestBankRates:
    """S9-TC-014 (P1): Banka faiz orani listesi veri butunlugu.

    S9 spesifik kontroller: siralamanin korunmasi, vade araliklari,
    min/max tutar tutarliligi.
    """

    def test_s9_tc_014_all_banks_have_required_fields(self) -> None:
        """Tum banka kayitlari gerekli alanlara sahip."""
        rates = get_bank_rates()
        for rate in rates:
            assert rate.bank_name
            assert rate.annual_rate > D("0")
            assert rate.min_term > 0
            assert rate.max_term > rate.min_term
            assert rate.min_amount > D("0")
            assert rate.max_amount > rate.min_amount
            assert rate.updated_at is not None

    def test_s9_tc_014_six_banks_present(self) -> None:
        """Tam 6 banka kaydi bulunmali."""
        rates = get_bank_rates()
        assert len(rates) == 6
        bank_names = {r.bank_name for r in rates}
        assert "Ziraat Bankası" in bank_names
        assert "Halkbank" in bank_names
        assert "Yapı Kredi" in bank_names

    def test_s9_tc_019_bank_rates_sorted_by_rate_possible(self) -> None:
        """S9-TC-019: Banka oranlari siraya konabilir (vitrin liste sayfasi icin)."""
        rates = get_bank_rates()
        sorted_rates = sorted(rates, key=lambda r: r.annual_rate)
        # En dusuk oran Ziraat olmali
        assert "Ziraat" in sorted_rates[0].bank_name
        # En yuksek oranlar kamu disinda (Is Bankasi veya Garanti)
        assert sorted_rates[-1].annual_rate > sorted_rates[0].annual_rate

    def test_bank_rates_immutability(self) -> None:
        """get_bank_rates() her cagirida bagimsiz kopya doner; mutasyon orijinali etkilemez."""
        rates1 = get_bank_rates()
        original_name = rates1[0].bank_name
        rates1.pop(0)
        rates2 = get_bank_rates()
        assert len(rates2) == 6
        assert rates2[0].bank_name == original_name
