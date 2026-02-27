"""
Emlak Teknoloji Platformu - Virtual Staging Service

Bos oda fotograflarini yapay zeka ile mobilyali hale getirir.
GPT-5-mini Vision ile oda analizi, gpt-image-1.x ile gorsel duzenleme.

Akis:
    1. analyze_room()    → Oda tipi, bosluk, zemin, isik analizi (Vision)
    2. build_staging_prompt() → Tarz + oda bilgisine gore prompt olusturma
    3. virtual_stage()   → Analiz + prompt + edit_image pipeline

Kullanim:
    from src.listings.staging_service import (
        analyze_room, virtual_stage, get_available_styles,
    )

    analysis = await analyze_room(image_bytes)
    if analysis.is_empty:
        result = await virtual_stage(image_bytes, style="modern")
        staged_png = result.staged_images[0]

Referans: TASK-115 (S8.5 + S8.6)
"""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass, field

import structlog

from src.services.openai_config import (
    IMAGE_MODEL,
    IMAGE_MODEL_MINI,
    QUALITY_HIGH,
    QUALITY_MEDIUM,
    SIZE_LANDSCAPE,
    TEXT_MODEL,
)
from src.services.openai_service import (
    analyze_image_async,
    edit_image_async,
)

logger = structlog.get_logger(__name__)


# ================================================================
# Dataclasses
# ================================================================


@dataclass(frozen=True, slots=True)
class RoomAnalysis:
    """
    Oda analiz sonucu — Vision API ciktisi.

    Attributes:
        room_type: salon, yatak_odasi, mutfak, banyo, cocuk_odasi,
                   calisma_odasi, yemek_odasi, antre
        is_empty: Oda mobilyasiz mi?
        floor_type: parke, seramik, laminat, mermer, hali, beton, bilinmiyor
        estimated_size: kucuk, orta, buyuk
        wall_color: Duvar rengi tahmini
        natural_light: dusuk, orta, yuksek
        window_count: Pencere sayisi
        special_features: somine, balkon, tavan kirisi vb.
    """

    room_type: str
    is_empty: bool
    floor_type: str = "bilinmiyor"
    estimated_size: str = "orta"
    wall_color: str = "beyaz"
    natural_light: str = "orta"
    window_count: int = 0
    special_features: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class StagingResult:
    """
    Virtual staging sonucu.

    Attributes:
        original_bytes: Orijinal gorsel verisi.
        staged_images: Sahnelenmiş gorsel(ler) PNG byte listesi.
        room_analysis: Oda analiz sonucu.
        style: Uygulanan tarz (modern, klasik, vb.).
        quality: Gorsel kalitesi (low, medium, high).
        processing_time_ms: Toplam islem suresi (milisaniye).
    """

    original_bytes: bytes
    staged_images: list[bytes]
    room_analysis: RoomAnalysis
    style: str
    quality: str
    processing_time_ms: int


# ================================================================
# Oda Tipi Sabitleri
# ================================================================

VALID_ROOM_TYPES: frozenset[str] = frozenset(
    {
        "salon",
        "yatak_odasi",
        "mutfak",
        "banyo",
        "cocuk_odasi",
        "calisma_odasi",
        "yemek_odasi",
        "antre",
    }
)

_ROOM_TYPE_ALIASES: dict[str, str] = {
    "living_room": "salon",
    "livingroom": "salon",
    "lounge": "salon",
    "bedroom": "yatak_odasi",
    "kitchen": "mutfak",
    "bathroom": "banyo",
    "kids_room": "cocuk_odasi",
    "children_room": "cocuk_odasi",
    "study": "calisma_odasi",
    "office": "calisma_odasi",
    "dining_room": "yemek_odasi",
    "hallway": "antre",
    "entrance": "antre",
    "entryway": "antre",
}


def _normalize_room_type(raw: str) -> str:
    """
    Ham oda tipi string'ini normalize eder.

    Vision API Ingilizce veya farkli format donebilir;
    alias haritasi ile standart Turkce tipe donusturulur.
    Bilinmeyen tip varsa 'salon' varsayilir.
    """
    normalized = raw.strip().lower().replace(" ", "_").replace("-", "_")

    if normalized in VALID_ROOM_TYPES:
        return normalized

    if normalized in _ROOM_TYPE_ALIASES:
        return _ROOM_TYPE_ALIASES[normalized]

    logger.warning(
        "staging_unknown_room_type",
        raw_room_type=raw,
        fallback="salon",
    )
    return "salon"


# ================================================================
# Style Prompts — 6 Tarz
# ================================================================

STYLE_PROMPTS: dict[str, dict[str, str]] = {
    "modern": {
        "name_tr": "Modern",
        "description": "Duz hatli kanepe, cam sehpa, metal lamba, notr tonlar",
        "furniture": (
            "a sleek low-profile sofa in light gray fabric, "
            "a glass coffee table with thin metal legs, "
            "a minimalist arc floor lamp with brushed nickel finish, "
            "a simple geometric area rug in muted tones, "
            "a couple of abstract art pieces on the wall"
        ),
        "palette": "neutral palette with white, gray, and warm beige accents",
    },
    "klasik": {
        "name_tr": "Klasik",
        "description": "Oymali koltuk, ahsap sehpa, kristal avize, sicak tonlar",
        "furniture": (
            "a carved wooden armchair with velvet upholstery, "
            "a rich mahogany coffee table, "
            "a crystal chandelier hanging from the ceiling, "
            "an ornate Persian-style area rug, "
            "classical framed oil paintings on the wall"
        ),
        "palette": "warm palette with burgundy, gold, cream, and dark wood tones",
    },
    "minimalist": {
        "name_tr": "Minimalist",
        "description": "Alcak kanepe, tek aksesuar, monokrom palet",
        "furniture": (
            "a very low-profile Japanese-style platform sofa in white, "
            "a single ceramic vase on the floor, "
            "clean empty walls with one small artwork, "
            "no clutter, maximum negative space"
        ),
        "palette": "monochrome palette with white, off-white, and soft gray",
    },
    "skandinav": {
        "name_tr": "Skandinav",
        "description": "Acik ahsap, beyaz, kurk, bitki, pastel",
        "furniture": (
            "a light oak wooden sofa frame with white linen cushions, "
            "a birch wood side table, "
            "a cozy sheepskin throw on the sofa, "
            "several green potted plants including a monstera, "
            "woven baskets for storage"
        ),
        "palette": "Scandinavian palette with white, light wood, sage green, and soft pink pastels",
    },
    "bohem": {
        "name_tr": "Bohem",
        "description": "Desenli kilim, bitki, makrame, rattan, toprak tonlari",
        "furniture": (
            "a colorful Moroccan-pattern area rug, "
            "many hanging and potted plants, "
            "a macrame wall hanging, "
            "a rattan peacock chair, "
            "floor cushions with ethnic patterns, "
            "woven jute poufs"
        ),
        "palette": "earthy bohemian palette with terracotta, mustard, sage, and burnt orange",
    },
    "endustriyel": {
        "name_tr": "Endustriyel",
        "description": "Deri kanepe, metal raf, Edison ampul, tugla",
        "furniture": (
            "a distressed brown leather Chesterfield sofa, "
            "an industrial metal pipe bookshelf, "
            "Edison bulb pendant lights hanging from exposed conduit, "
            "a reclaimed wood and iron coffee table, "
            "exposed brick texture on walls"
        ),
        "palette": "industrial palette with dark brown, black iron, warm wood, and raw concrete gray",
    },
}

VALID_STYLES: frozenset[str] = frozenset(STYLE_PROMPTS.keys())


# ================================================================
# Room Type → Furniture Context
# ================================================================

_ROOM_FURNITURE_CONTEXT: dict[str, str] = {
    "salon": "living room furniture: sofa, coffee table, side table, floor lamp, area rug",
    "yatak_odasi": "bedroom furniture: bed with headboard, nightstands, dresser, table lamp, soft rug",
    "mutfak": "kitchen furnishings: dining table with chairs, pendant light, small countertop items",
    "banyo": "bathroom accessories: towel rack, bath mat, small shelf, decorative items",
    "cocuk_odasi": "children's room: colorful bed, toy shelf, soft rug, playful wall art",
    "calisma_odasi": "home office: desk, ergonomic chair, bookshelf, desk lamp, small plant",
    "yemek_odasi": "dining room: dining table with chairs, sideboard, chandelier, table runner",
    "antre": "entryway: console table, mirror, coat rack, small bench, shoe storage",
}


# ================================================================
# A) Room Analysis — Vision API
# ================================================================

_ROOM_ANALYSIS_PROMPT = """\
You are an expert interior design AI. Analyze this room photograph and return a JSON object with EXACTLY these fields:

{
  "room_type": "<one of: salon, yatak_odasi, mutfak, banyo, cocuk_odasi, calisma_odasi, yemek_odasi, antre>",
  "is_empty": <true if the room has NO furniture or is mostly empty, false if furnished>,
  "floor_type": "<one of: parke, seramik, laminat, mermer, hali, beton, bilinmiyor>",
  "estimated_size": "<one of: kucuk, orta, buyuk>",
  "wall_color": "<dominant wall color in Turkish, e.g. beyaz, krem, gri, bej>",
  "natural_light": "<one of: dusuk, orta, yuksek>",
  "window_count": <integer, number of visible windows>,
  "special_features": [<list of special features like "somine", "balkon", "tavan_kirisi", "sutun">]
}

Rules:
- is_empty MUST be true ONLY if there is genuinely no furniture in the room.
- If you see ANY significant furniture (sofa, table, bed, etc.), set is_empty to false.
- Use Turkish values for room_type and floor_type as specified above.
- Return ONLY the JSON object, no extra text.
"""


async def analyze_room(
    image_bytes: bytes,
    *,
    model: str = TEXT_MODEL,
) -> RoomAnalysis:
    """
    Oda fotografini GPT-5-mini Vision ile analiz eder.

    Args:
        image_bytes: Gorsel verisi (JPEG, PNG, WebP).
        model: Vision destekli model.

    Returns:
        RoomAnalysis — oda tipi, bosluk durumu, zemin, isik analizi.

    Raises:
        OpenAIServiceError: API hatasi.
        OpenAIInvalidImageError: Gecersiz gorsel.
    """
    logger.info(
        "staging_room_analysis_start",
        image_size_bytes=len(image_bytes),
        model=model,
    )

    raw_result = await analyze_image_async(
        image_bytes,
        _ROOM_ANALYSIS_PROMPT,
        model=model,
        detail="high",
    )

    # Parse — Vision API JSON object dondurur
    room_type = _normalize_room_type(raw_result.get("room_type", "salon"))
    is_empty = bool(raw_result.get("is_empty", False))

    # floor_type normalizasyonu
    floor_type = str(raw_result.get("floor_type", "bilinmiyor")).strip().lower()
    valid_floors = {"parke", "seramik", "laminat", "mermer", "hali", "beton", "bilinmiyor"}
    if floor_type not in valid_floors:
        floor_type = "bilinmiyor"

    # estimated_size normalizasyonu
    estimated_size = str(raw_result.get("estimated_size", "orta")).strip().lower()
    if estimated_size not in {"kucuk", "orta", "buyuk"}:
        estimated_size = "orta"

    # natural_light normalizasyonu
    natural_light = str(raw_result.get("natural_light", "orta")).strip().lower()
    if natural_light not in {"dusuk", "orta", "yuksek"}:
        natural_light = "orta"

    # window_count — sayi olarak garantile
    try:
        window_count = max(0, int(raw_result.get("window_count", 0)))
    except (TypeError, ValueError):
        window_count = 0

    # special_features — liste garantile
    raw_features = raw_result.get("special_features", [])
    if isinstance(raw_features, list):
        special_features = [str(f).strip() for f in raw_features if f]
    else:
        special_features = []

    analysis = RoomAnalysis(
        room_type=room_type,
        is_empty=is_empty,
        floor_type=floor_type,
        estimated_size=estimated_size,
        wall_color=str(raw_result.get("wall_color", "beyaz")).strip(),
        natural_light=natural_light,
        window_count=window_count,
        special_features=special_features,
    )

    logger.info(
        "staging_room_analysis_complete",
        room_type=analysis.room_type,
        is_empty=analysis.is_empty,
        floor_type=analysis.floor_type,
        estimated_size=analysis.estimated_size,
        natural_light=analysis.natural_light,
    )

    return analysis


# ================================================================
# B) Prompt Builder
# ================================================================


def build_staging_prompt(
    room_type: str,
    style: str,
    analysis: RoomAnalysis,
) -> str:
    """
    Oda tipi, tarz ve analiz sonucuna gore sahneleme prompt'u olusturur.

    Prompt yapisi:
        1. Genel talimat (bos odayi mobilyalandir)
        2. Oda konteksti (salon -> kanepe, sehpa ...)
        3. Tarz mobilyalari (modern -> duz hatli kanepe ...)
        4. Renk paleti
        5. Oda ozellikleri (zemin, isik, ozel ozellikler)

    Args:
        room_type: Normalize edilmis oda tipi.
        style: Tarz ID (modern, klasik, vb.).
        analysis: RoomAnalysis dataclass.

    Returns:
        OpenAI edit_image icin hazir prompt string.

    Raises:
        ValueError: Gecersiz tarz.
    """
    if style not in STYLE_PROMPTS:
        valid = ", ".join(sorted(STYLE_PROMPTS.keys()))
        raise ValueError(f"Gecersiz tarz: '{style}'. Gecerli tarzlar: {valid}")

    style_data = STYLE_PROMPTS[style]
    room_context = _ROOM_FURNITURE_CONTEXT.get(room_type, _ROOM_FURNITURE_CONTEXT["salon"])

    # Oda ozellik bilgileri
    room_details_parts: list[str] = []
    if analysis.floor_type != "bilinmiyor":
        room_details_parts.append(f"The floor is {analysis.floor_type}")
    if analysis.wall_color:
        room_details_parts.append(f"walls are {analysis.wall_color}")
    if analysis.natural_light == "yuksek":
        room_details_parts.append("the room has abundant natural light")
    elif analysis.natural_light == "dusuk":
        room_details_parts.append("the room has limited natural light, add warm lighting")
    if analysis.special_features:
        features_str = ", ".join(analysis.special_features)
        room_details_parts.append(f"special features: {features_str}")

    room_details = ". ".join(room_details_parts) + "." if room_details_parts else ""

    prompt = (
        f"Transform this empty room into a beautifully furnished {style_data['name_tr'].lower()} style "
        f"interior. This is a {room_context}. "
        f"Place the following furniture naturally in the room: {style_data['furniture']}. "
        f"Use a {style_data['palette']}. "
        f"The room size is {analysis.estimated_size}. "
        f"{room_details} "
        "Keep the original room structure, walls, windows, and architectural elements intact. "
        "The furniture must look photorealistic and properly scaled to the room. "
        "Maintain correct perspective and lighting consistency with the original photograph. "
        "Output a high-quality photorealistic interior photograph."
    )

    return prompt.strip()


# ================================================================
# C) Staging Pipeline
# ================================================================


async def virtual_stage(
    image_bytes: bytes,
    style: str,
    *,
    quality: str = QUALITY_MEDIUM,
    n: int = 1,
    image_model: str = IMAGE_MODEL,
    vision_model: str = TEXT_MODEL,
) -> StagingResult:
    """
    Bos oda fotografini verilen tarzda sahneler (end-to-end pipeline).

    Akis:
        1. analyze_room() → Oda analizi
        2. is_empty kontrolu → Bos degilse ValueError
        3. build_staging_prompt() → Tarz prompt olustur
        4. edit_image_async() → OpenAI ile gorsel duzenleme
        5. StagingResult dondur

    Args:
        image_bytes: Orijinal gorsel verisi (JPEG, PNG, WebP).
        style: Sahneleme tarzi (modern, klasik, minimalist, skandinav, bohem, endustriyel).
        quality: Gorsel kalitesi (low, medium, high).
        n: Uretilecek varyasyon sayisi (1-4).
        image_model: Gorsel duzenleme modeli.
        vision_model: Oda analizi modeli.

    Returns:
        StagingResult — sahnelenmiş gorseller, analiz, sure.

    Raises:
        ValueError: Oda bos degil veya gecersiz tarz.
        OpenAIServiceError: API hatasi.
        OpenAIInvalidImageError: Gecersiz gorsel.
        OpenAIContentFilterError: Icerik filtrelendi.
    """
    start_ms = _now_ms()

    # Tarz validasyonu — erken fail
    if style not in VALID_STYLES:
        valid = ", ".join(sorted(VALID_STYLES))
        raise ValueError(f"Gecersiz tarz: '{style}'. Gecerli tarzlar: {valid}")

    logger.info(
        "staging_pipeline_start",
        style=style,
        quality=quality,
        n=n,
        image_model=image_model,
        image_size_bytes=len(image_bytes),
    )

    # 1. Oda analizi
    analysis = await analyze_room(image_bytes, model=vision_model)

    # 2. Bos oda kontrolu
    if not analysis.is_empty:
        logger.warning(
            "staging_room_not_empty",
            room_type=analysis.room_type,
        )
        raise ValueError(
            "Oda bos degil. Virtual staging yalnizca bos veya mobilyasiz odalar icin kullanilabilir."
        )

    # 3. Prompt olustur
    prompt = build_staging_prompt(analysis.room_type, style, analysis)

    logger.debug(
        "staging_prompt_built",
        prompt_length=len(prompt),
        room_type=analysis.room_type,
        style=style,
    )

    # 4. Gorsel duzenleme
    staged_images = await edit_image_async(
        image_bytes,
        prompt,
        model=image_model,
        size=SIZE_LANDSCAPE,
        quality=quality,
        n=n,
    )

    elapsed_ms = _now_ms() - start_ms

    logger.info(
        "staging_pipeline_complete",
        style=style,
        room_type=analysis.room_type,
        image_count=len(staged_images),
        processing_time_ms=elapsed_ms,
        total_output_bytes=sum(len(img) for img in staged_images),
    )

    return StagingResult(
        original_bytes=image_bytes,
        staged_images=staged_images,
        room_analysis=analysis,
        style=style,
        quality=quality,
        processing_time_ms=elapsed_ms,
    )


# ================================================================
# D) Yardimci Fonksiyonlar
# ================================================================


def get_available_styles() -> list[dict[str, str]]:
    """
    Kullanilabilir tum tarzlari dondurur.

    Returns:
        Her eleman: {"id": "modern", "name_tr": "Modern", "description": "..."}
    """
    return [
        {
            "id": style_id,
            "name_tr": style_data["name_tr"],
            "description": style_data["description"],
        }
        for style_id, style_data in STYLE_PROMPTS.items()
    ]


def get_model_for_plan(plan: str) -> str:
    """
    Abonelik planina gore gorsel duzenleme modelini belirler.

    Args:
        plan: Plan tipi (starter, pro, elite).

    Returns:
        Model adi string.
        - Starter: gpt-image-1-mini (hizli, dusuk maliyet)
        - Pro / Elite: gpt-image-1.5 (yuksek kalite)
    """
    plan_lower = plan.strip().lower()
    if plan_lower == "starter":
        return IMAGE_MODEL_MINI
    return IMAGE_MODEL


def get_quality_for_plan(plan: str) -> str:
    """
    Abonelik planina gore gorsel kalitesini belirler.

    Args:
        plan: Plan tipi (starter, pro, elite).

    Returns:
        Kalite string.
        - Starter / Pro: medium
        - Elite: high
    """
    plan_lower = plan.strip().lower()
    if plan_lower == "elite":
        return QUALITY_HIGH
    return QUALITY_MEDIUM


def staged_image_to_base64(image_bytes: bytes) -> str:
    """
    Gorsel byte verisini base64 string'e donusturur.

    Args:
        image_bytes: PNG gorsel verisi.

    Returns:
        Base64 encode edilmis string.
    """
    return base64.b64encode(image_bytes).decode("utf-8")


# ================================================================
# Internal Helpers
# ================================================================


def _now_ms() -> int:
    """Milisaniye cinsinden epoch zamani."""
    return int(time.monotonic() * 1000)
