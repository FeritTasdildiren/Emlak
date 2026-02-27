"""
Emlak Teknoloji Platformu - Listing Assistant Service

Yapay zeka destekli ilan metni uretim servisi.
3 farkli ton (kurumsal, samimi, acil) ile Turkce ilan metni, baslik,
one cikan ozellikler ve SEO anahtar kelimeleri uretir.

Kullanim:
    from src.listings.listing_assistant_service import (
        generate_listing_text,
        get_available_tones,
    )

    result = await generate_listing_text(request)
    tones = get_available_tones()

Mimari:
    - openai_service.generate_text_async() wrapper — JSON response parse
    - Ton bazli prompt sablonlari (TONE_PROMPTS dict)
    - SEO optimizasyonu: baslik formatlama + anahtar kelime cikarimi
    - validate_request() — is mantigi dogrulamasi (Pydantic disinda)

Referans: TASK-118 (S8.2 + S8.3)
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

import structlog

from src.services.openai_service import generate_text_async

if TYPE_CHECKING:
    from src.listings.listing_assistant_schemas import (
        ListingTextRequest,
        RegenerateRequest,
    )

logger = structlog.get_logger(__name__)


# ================================================================
# Ton Tanimlari
# ================================================================

# Her ton icin: system_prompt + user_prompt_template
# System prompt GPT'ye rolunu tanimlar; user prompt ilan detaylarini icerir.
TONE_PROMPTS: dict[str, dict[str, str]] = {
    "kurumsal": {
        "system_prompt": (
            "Sen deneyimli bir emlak danismaninin profesyonel ilan editoususun. "
            "Yazdigin metinler kurumsal, guvence veren ve rakamlara dayali olur. "
            "Teknik detaylari on plana cikarir, yatirim degerini vurgularsin. "
            "'Yatirim degeri yuksek', 'prestijli konum', 'teknik altyapi' gibi ifadeler kullanirsin. "
            "Her zaman TURKCE yaz. Abartili pazarlama dilinden kacin, somut bilgi ver."
        ),
        "user_prompt_template": (
            "Asagidaki mulk bilgilerini kullanarak KURUMSAL tonda bir emlak ilani yaz.\n\n"
            "MULK BILGILERI:\n{property_details}\n\n"
            "KURALLAR:\n"
            "- Baslik: Kisa, net, SEO uyumlu (maks 80 karakter)\n"
            "- Aciklama: Profesyonel dil, 300-600 kelime, rakam ve teknik detay odakli\n"
            "- 3-6 one cikan ozellik maddesi\n"
            "- 5-10 SEO anahtar kelimesi\n"
            "- Yatirim potansiyelini vurgula\n"
            "- Konum avantajlarini belirt\n\n"
            "YANIT FORMATI (JSON):\n"
            "{{\n"
            '  "title": "...",\n'
            '  "description": "...",\n'
            '  "highlights": ["...", "..."],\n'
            '  "seo_keywords": ["...", "..."]\n'
            "}}"
        ),
    },
    "samimi": {
        "system_prompt": (
            "Sen sicakkanlı bir emlak danismaninin yaratici ilan yazarisin. "
            "Yazdigin metinler samimi, sicak ve ev hissi veren bir dilde olur. "
            "Ailelere, ciftlere ve ev arayanların duygularina hitap edersin. "
            "'Ailenizle mutlu olacaginiz', 'evinizin sicakligi', 'huzurlu yasam' gibi ifadeler kullanirsin. "
            "Komsuluğu ve yasam alanlarini betimlersin. "
            "Her zaman TURKCE yaz. Samimi ama güvenilir ol."
        ),
        "user_prompt_template": (
            "Asagidaki mulk bilgilerini kullanarak SAMIMI ve SICAK tonda bir emlak ilani yaz.\n\n"
            "MULK BILGILERI:\n{property_details}\n\n"
            "KURALLAR:\n"
            "- Baslik: Sicak, davetkar, ev hissi veren (maks 80 karakter)\n"
            "- Aciklama: Samimi dil, 300-600 kelime, yasam deneyimini anlat\n"
            "- 3-6 one cikan ozellik maddesi (yasam odakli)\n"
            "- 5-10 SEO anahtar kelimesi\n"
            "- Mahalle yasantisini ve komsuluğu vurgula\n"
            "- Evin sicakligi ve konforunu hissettir\n\n"
            "YANIT FORMATI (JSON):\n"
            "{{\n"
            '  "title": "...",\n'
            '  "description": "...",\n'
            '  "highlights": ["...", "..."],\n'
            '  "seo_keywords": ["...", "..."]\n'
            "}}"
        ),
    },
    "acil": {
        "system_prompt": (
            "Sen hizli karar aldiran bir emlak pazarlama uzmanisın. "
            "Yazdigin metinler kisa, net ve aciliyet duygusu yaratan bir dilde olur. "
            "FOMO (firsati kacirma korkusu) etkisi yaratirsin ama dürüst kalirsin. "
            "'Kacirilmayacak firsat', 'sinirli sure', 'hemen arayin' gibi ifadeler kullanirsin. "
            "Kisa cümleler, etkili basliklar, aksiyon odakli dil kullanirsin. "
            "Her zaman TURKCE yaz. Abartma ama aciliyeti hissettir."
        ),
        "user_prompt_template": (
            "Asagidaki mulk bilgilerini kullanarak ACIL ve FIRSATCI tonda bir emlak ilani yaz.\n\n"
            "MULK BILGILERI:\n{property_details}\n\n"
            "KURALLAR:\n"
            "- Baslik: Dikkat cekici, aciliyet hissi veren (maks 80 karakter)\n"
            "- Aciklama: Kisa ve etkili, 200-400 kelime, aksiyon odakli\n"
            "- 3-6 one cikan ozellik maddesi (firsat vurgusu)\n"
            "- 5-10 SEO anahtar kelimesi\n"
            "- Fiyat avantajini ve firsati vurgula\n"
            "- Aciliyet hissi yarat, hemen iletisime gecmeye tesvik et\n\n"
            "YANIT FORMATI (JSON):\n"
            "{{\n"
            '  "title": "...",\n'
            '  "description": "...",\n'
            '  "highlights": ["...", "..."],\n'
            '  "seo_keywords": ["...", "..."]\n'
            "}}"
        ),
    },
}

# Ton listesi — GET /tones endpoint'i icin
_TONE_LIST: list[dict[str, str]] = [
    {
        "id": "kurumsal",
        "name_tr": "Kurumsal",
        "description": "Profesyonel, rakam odakli, teknik detay ve yatirim degeri vurgusu",
        "example_phrase": "Yatirim degeri yuksek, prestijli konumda 3+1 rezidans daire.",
    },
    {
        "id": "samimi",
        "name_tr": "Samimi",
        "description": "Sicak, ev hissi veren, aile ve yasam odakli anlatim",
        "example_phrase": "Ailenizle mutlu olacaginiz, huzurlu bir yuva sizi bekliyor.",
    },
    {
        "id": "acil",
        "name_tr": "Acil Satis",
        "description": "Kisa, net, firsat vurgusu ve aciliyet hissi",
        "example_phrase": "Kacirilmayacak firsat! Bu fiyata bu lokasyonda son daire.",
    },
]


# ================================================================
# Yardimci Fonksiyonlar
# ================================================================


def get_available_tones() -> list[dict[str, str]]:
    """
    Kullanilabilir tum ton seceneklerini dondurur.

    Returns:
        Ton bilgileri listesi (id, name_tr, description, example_phrase).
    """
    return _TONE_LIST.copy()


def validate_request(request: ListingTextRequest | RegenerateRequest) -> None:
    """
    Ilan metni istegini is mantigiyla dogrular.

    Pydantic field-level dogrulama disinda kalan mantiksal kurallari kontrol eder.

    Args:
        request: Ilan metni uretim veya yeniden uretim istegi.

    Raises:
        ValueError: Is mantigi dogrulama hatasi.
    """
    # Ton gecerliligi (Pydantic Literal ile de kontrol edilir, ek guvenlik)
    if request.tone not in TONE_PROMPTS:
        valid_tones = list(TONE_PROMPTS.keys())
        raise ValueError(f"Gecersiz ton: '{request.tone}'. Gecerli tonlar: {valid_tones}")

    # Net metrekare mantik kontrolu
    if request.gross_sqm is not None and request.net_sqm > request.gross_sqm:
        raise ValueError(
            f"Net metrekare ({request.net_sqm}) brut metrekareden ({request.gross_sqm}) "
            "buyuk olamaz."
        )

    # Kat mantik kontrolu
    if (
        request.floor is not None
        and request.total_floors is not None
        and request.floor > request.total_floors
    ):
        raise ValueError(
            f"Bulundugu kat ({request.floor}) toplam kat sayisindan ({request.total_floors}) "
            "buyuk olamaz."
        )


def _format_property_details(request: ListingTextRequest | RegenerateRequest) -> str:
    """
    Mulk bilgilerini okunabilir formata donusturur.

    OpenAI prompt'unda kullanilmak uzere structured text uretir.
    Sadece dolu alanlari dahil eder.

    Args:
        request: Ilan metni istegi.

    Returns:
        Formatted property details string.
    """
    lines: list[str] = [
        f"- Mulk Tipi: {request.property_type}",
        f"- Ilce: {request.district}",
        f"- Mahalle: {request.neighborhood}",
        f"- Oda Sayisi: {request.room_count}",
        f"- Net Metrekare: {request.net_sqm} m²",
        f"- Fiyat: {request.price:,.0f} TL",
    ]

    # Opsiyonel alanlar — sadece dolu olanlar eklenir
    if request.gross_sqm is not None:
        lines.append(f"- Brut Metrekare: {request.gross_sqm} m²")
    if request.floor is not None:
        floor_str = "Giriş kat" if request.floor == 0 else f"{request.floor}. kat"
        if request.total_floors is not None:
            floor_str += f" / {request.total_floors} katli bina"
        lines.append(f"- Kat: {floor_str}")
    elif request.total_floors is not None:
        lines.append(f"- Toplam Kat: {request.total_floors}")
    if request.building_age is not None:
        if request.building_age == 0:
            lines.append("- Bina Yasi: Sifir bina (yeni)")
        else:
            lines.append(f"- Bina Yasi: {request.building_age} yil")
    if request.heating_type:
        lines.append(f"- Isitma: {request.heating_type}")

    # Boolean ozellikler
    features: list[str] = []
    if request.has_elevator:
        features.append("Asansor")
    if request.has_parking:
        features.append("Otopark")
    if request.has_balcony:
        features.append("Balkon")
    if request.has_garden:
        features.append("Bahce")
    if request.has_pool:
        features.append("Havuz")
    if request.is_furnished:
        features.append("Esyali")
    if request.has_security:
        features.append("Guvenlik / Site icinde")
    if features:
        lines.append(f"- Ozellikler: {', '.join(features)}")

    if request.view_type:
        lines.append(f"- Manzara: {request.view_type}")
    if request.additional_notes:
        lines.append(f"- Ek Notlar: {request.additional_notes}")

    return "\n".join(lines)


def build_listing_prompt(
    request: ListingTextRequest | RegenerateRequest,
    tone: str,
) -> tuple[str, str]:
    """
    Ilan metni uretimi icin system_prompt ve user_prompt olusturur.

    Args:
        request: Ilan metni istegi.
        tone: Ton secimi (kurumsal, samimi, acil).

    Returns:
        (system_prompt, user_prompt) tuple.

    Raises:
        ValueError: Gecersiz ton secimi.
    """
    if tone not in TONE_PROMPTS:
        valid_tones = list(TONE_PROMPTS.keys())
        raise ValueError(f"Gecersiz ton: '{tone}'. Gecerli tonlar: {valid_tones}")

    tone_config = TONE_PROMPTS[tone]
    property_details = _format_property_details(request)

    system_prompt = tone_config["system_prompt"]
    user_prompt = tone_config["user_prompt_template"].format(
        property_details=property_details,
    )

    return system_prompt, user_prompt


def seo_optimize_title(raw_title: str, request: ListingTextRequest | RegenerateRequest) -> str:
    """
    Ham basligi SEO formatina uygun hale getirir.

    Format: '{Oda} {Tip} {Mahalle} {Ilce} - {One cikan ozellik}'

    Eger GPT'nin urettigi baslik zaten bu formata uygunsa dokunmaz.
    Degilse yeniden formatlar ama GPT basligindaki one cikan ozelligi korur.

    Args:
        raw_title: GPT'nin urettigi ham baslik.
        request: Ilan istegi (alan bilgileri icin).

    Returns:
        SEO-optimize edilmis baslik.
    """
    # Gerekli bilesenler mevcut mu kontrol et
    has_room = request.room_count in raw_title
    has_district = request.district.lower() in raw_title.lower()

    # Eger baslik zaten temel bilgileri iceriyorsa, fazla mudahale etme
    if has_room and has_district:
        return raw_title.strip()[:120]

    # One cikan ozelligi GPT basligindan cikar
    # Basligin sonundaki ' - ' den sonrasini al veya tamamini kullan
    highlight = raw_title
    if " - " in raw_title:
        parts = raw_title.split(" - ", 1)
        highlight = parts[1].strip() if len(parts) > 1 else raw_title

    # Tip esleme
    type_map: dict[str, str] = {
        "daire": "Daire",
        "villa": "Villa",
        "rezidans": "Rezidans",
        "mustakil": "Mustakil Ev",
        "arsa": "Arsa",
    }
    prop_type = type_map.get(request.property_type.lower(), request.property_type)

    optimized = (
        f"{request.room_count} {prop_type} {request.neighborhood} {request.district} - {highlight}"
    )

    return optimized.strip()[:120]


def extract_seo_keywords(
    request: ListingTextRequest | RegenerateRequest,
    description: str,
) -> list[str]:
    """
    Ilan bilgileri ve aciklamadan SEO anahtar kelimelerini cikarir.

    GPT'nin urettigi keyword'leri kullanir, eksikleri tamamlar.

    Args:
        request: Ilan istegi.
        description: Uretilen ilan aciklamasi.

    Returns:
        5-10 adet SEO anahtar kelime listesi.
    """
    keywords: list[str] = []

    # Temel keyword'ler — her zaman dahil
    keywords.append(f"satilik {request.property_type} {request.district.lower()}")
    keywords.append(
        f"{request.room_count} {request.property_type.lower()} {request.district.lower()}"
    )
    keywords.append(f"{request.neighborhood.lower()} {request.property_type.lower()}")
    keywords.append(f"satilik {request.property_type} {request.neighborhood.lower()}")

    # Opsiyonel keyword'ler
    if request.view_type:
        keywords.append(f"{request.view_type} manzarali {request.property_type.lower()}")
    if request.has_pool:
        keywords.append(f"havuzlu {request.property_type.lower()}")
    if request.has_garden:
        keywords.append(f"bahceli {request.property_type.lower()}")
    if request.building_age is not None and request.building_age == 0:
        keywords.append(f"sifir {request.property_type.lower()} {request.district.lower()}")

    # Fiyat araligi keyword
    price_m = request.price / 1_000_000
    if price_m >= 1:
        keywords.append(f"{price_m:.0f} milyon tl {request.property_type.lower()}")

    # Fazla ise kes, az ise aciklamadan cikar
    if len(keywords) < 5 and description:
        # Aciklamadaki onemli kelime gruplarini ekle
        location_kw = f"{request.district.lower()} emlak"
        if location_kw not in keywords:
            keywords.append(location_kw)

    return keywords[:10]


def _parse_llm_response(raw_text: str) -> dict[str, Any]:
    """
    LLM yanitini JSON olarak parse eder.

    GPT bazen JSON blogunun etrafina markdown code fence ekler.
    Bu durumu handle eder.

    Args:
        raw_text: LLM'den gelen ham yani.

    Returns:
        Parsed JSON dict.

    Raises:
        ValueError: JSON parse edilemedi.
    """
    # Markdown code fence temizle: ```json ... ``` veya ``` ... ```
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        # Ilk satiri (```json veya ```) kaldir
        lines = cleaned.split("\n", 1)
        if len(lines) > 1:
            cleaned = lines[1]
        # Son ``` 'i kaldir
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3].rstrip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        # Regex ile JSON blogu cikar
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        raise ValueError(
            f"LLM yaniti JSON olarak parse edilemedi. Ham yanit: {raw_text[:500]}"
        ) from exc


# ================================================================
# Ana Uretim Fonksiyonu
# ================================================================


async def generate_listing_text(
    request: ListingTextRequest | RegenerateRequest,
) -> dict[str, Any]:
    """
    Ilan metni uretir — ana servis fonksiyonu.

    Akis:
        1. validate_request() — is mantigi dogrulama
        2. build_listing_prompt() — ton bazli prompt olustur
        3. generate_text_async() — OpenAI API cagir
        4. _parse_llm_response() — JSON parse
        5. seo_optimize_title() — baslik SEO iyilestir
        6. extract_seo_keywords() — keyword zenginlestir
        7. ListingTextResult dict dondur

    Args:
        request: Ilan metni istegi (ListingTextRequest veya RegenerateRequest).

    Returns:
        Dict: title, description, highlights, seo_keywords, tone_used, token_usage.

    Raises:
        ValueError: Dogrulama hatasi veya LLM parse hatasi.
        OpenAIServiceError: OpenAI API hatasi.
    """
    # 1. Dogrulama
    validate_request(request)

    tone = request.tone

    # 2. Prompt olustur
    system_prompt, user_prompt = build_listing_prompt(request, tone)

    logger.info(
        "listing_text_generation_started",
        tone=tone,
        property_type=request.property_type,
        district=request.district,
        neighborhood=request.neighborhood,
    )

    # 3. OpenAI API cagir
    raw_response = await generate_text_async(
        user_prompt,
        system_prompt=system_prompt,
        temperature=0.8,
        max_tokens=2048,
    )

    # Token kullanimi tahmini (ortalama 1.3 token/kelime Turkce icin)
    prompt_tokens = len((system_prompt + user_prompt).split()) * 2
    response_tokens = len(raw_response.split()) * 2
    estimated_tokens = prompt_tokens + response_tokens

    # 4. JSON parse
    parsed = _parse_llm_response(raw_response)

    title = parsed.get("title", "")
    description = parsed.get("description", "")
    highlights = parsed.get("highlights", [])
    llm_keywords = parsed.get("seo_keywords", [])

    # 5. SEO baslik optimize
    optimized_title = seo_optimize_title(title, request)

    # 6. SEO keyword zenginlestir
    base_keywords = extract_seo_keywords(request, description)
    # LLM keyword'lerini ekle (tekrar etmeyenleri)
    all_keywords = list(base_keywords)
    existing_lower = {k.lower() for k in all_keywords}
    for kw in llm_keywords:
        if isinstance(kw, str) and kw.lower() not in existing_lower:
            all_keywords.append(kw)
            existing_lower.add(kw.lower())
    final_keywords = all_keywords[:10]

    # Highlights kontrolu
    if not isinstance(highlights, list):
        highlights = []
    highlights = [str(h) for h in highlights if h][:6]

    logger.info(
        "listing_text_generation_completed",
        tone=tone,
        title_length=len(optimized_title),
        description_length=len(description),
        highlights_count=len(highlights),
        keywords_count=len(final_keywords),
        estimated_tokens=estimated_tokens,
    )

    return {
        "title": optimized_title,
        "description": description,
        "highlights": highlights,
        "seo_keywords": final_keywords,
        "tone_used": tone,
        "token_usage": estimated_tokens,
    }
