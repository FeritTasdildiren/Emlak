// ---------------------------------------------------------------------------
// Merkezi konum verisi — Property Form ve Ilan Asistani ortak kullanir
// ---------------------------------------------------------------------------

export interface CityData {
  value: string
  label: string
}

export interface DistrictData {
  value: string
  label: string
}

// ---------------------------------------------------------------------------
// Iller
// ---------------------------------------------------------------------------

export const cities: CityData[] = [
  { value: "istanbul", label: "İstanbul" },
  { value: "ankara", label: "Ankara" },
  { value: "izmir", label: "İzmir" },
]

// ---------------------------------------------------------------------------
// İlçeler — il bazında
// ---------------------------------------------------------------------------

export const districtsByCity: Record<string, DistrictData[]> = {
  istanbul: [
    { value: "Adalar", label: "Adalar" },
    { value: "Arnavutkoy", label: "Arnavutköy" },
    { value: "Atasehir", label: "Ataşehir" },
    { value: "Avcilar", label: "Avcılar" },
    { value: "Bagcilar", label: "Bağcılar" },
    { value: "Bahcelievler", label: "Bahçelievler" },
    { value: "Bakirkoy", label: "Bakırköy" },
    { value: "Basaksehir", label: "Başakşehir" },
    { value: "Bayrampasa", label: "Bayrampaşa" },
    { value: "Besiktas", label: "Beşiktaş" },
    { value: "Beykoz", label: "Beykoz" },
    { value: "Beylikduzu", label: "Beylikdüzü" },
    { value: "Beyoglu", label: "Beyoğlu" },
    { value: "Buyukcekmece", label: "Büyükçekmece" },
    { value: "Catalca", label: "Çatalca" },
    { value: "Cekmekoy", label: "Çekmeköy" },
    { value: "Esenler", label: "Esenler" },
    { value: "Esenyurt", label: "Esenyurt" },
    { value: "Eyupsultan", label: "Eyüpsultan" },
    { value: "Fatih", label: "Fatih" },
    { value: "Gaziosmanpasa", label: "Gaziosmanpaşa" },
    { value: "Gungoren", label: "Güngören" },
    { value: "Kadikoy", label: "Kadıköy" },
    { value: "Kagithane", label: "Kağıthane" },
    { value: "Kartal", label: "Kartal" },
    { value: "Kucukcekmece", label: "Küçükçekmece" },
    { value: "Maltepe", label: "Maltepe" },
    { value: "Pendik", label: "Pendik" },
    { value: "Sancaktepe", label: "Sancaktepe" },
    { value: "Sariyer", label: "Sarıyer" },
    { value: "Silivri", label: "Silivri" },
    { value: "Sultanbeyli", label: "Sultanbeyli" },
    { value: "Sultangazi", label: "Sultangazi" },
    { value: "Sile", label: "Şile" },
    { value: "Sisli", label: "Şişli" },
    { value: "Tuzla", label: "Tuzla" },
    { value: "Umraniye", label: "Ümraniye" },
    { value: "Uskudar", label: "Üsküdar" },
    { value: "Zeytinburnu", label: "Zeytinburnu" },
  ],
  ankara: [
    { value: "Akyurt", label: "Akyurt" },
    { value: "Altindag", label: "Altındağ" },
    { value: "Ayas", label: "Ayaş" },
    { value: "Bala", label: "Bala" },
    { value: "Beypazari", label: "Beypazarı" },
    { value: "Camlidere", label: "Çamlıdere" },
    { value: "Cankaya", label: "Çankaya" },
    { value: "Cubuk", label: "Çubuk" },
    { value: "Elmadag", label: "Elmadağ" },
    { value: "Etimesgut", label: "Etimesgut" },
    { value: "Evren", label: "Evren" },
    { value: "Golbasi", label: "Gölbaşı" },
    { value: "Gudul", label: "Güdül" },
    { value: "Haymana", label: "Haymana" },
    { value: "Kahramankazan", label: "Kahramankazan" },
    { value: "Kalecik", label: "Kalecik" },
    { value: "Kecioren", label: "Keçiören" },
    { value: "Kizilcahamam", label: "Kızılcahamam" },
    { value: "Mamak", label: "Mamak" },
    { value: "Nallihan", label: "Nallıhan" },
    { value: "Polatli", label: "Polatlı" },
    { value: "Pursaklar", label: "Pursaklar" },
    { value: "Sincan", label: "Sincan" },
    { value: "Sereflikochsar", label: "Şereflikoçhisar" },
    { value: "Yenimahalle", label: "Yenimahalle" },
  ],
  izmir: [
    { value: "Aliaga", label: "Aliağa" },
    { value: "Balcova", label: "Balçova" },
    { value: "Bayindir", label: "Bayındır" },
    { value: "Bayrakli", label: "Bayraklı" },
    { value: "Bergama", label: "Bergama" },
    { value: "Beydag", label: "Beydağ" },
    { value: "Bornova", label: "Bornova" },
    { value: "Buca", label: "Buca" },
    { value: "Cesme", label: "Çeşme" },
    { value: "Cigli", label: "Çiğli" },
    { value: "Dikili", label: "Dikili" },
    { value: "Foca", label: "Foça" },
    { value: "Gaziemir", label: "Gaziemir" },
    { value: "Guzelbahce", label: "Güzelbahçe" },
    { value: "Karabaglar", label: "Karabağlar" },
    { value: "Karsiyaka", label: "Karşıyaka" },
    { value: "Karaburun", label: "Karaburun" },
    { value: "Kemalpasa", label: "Kemalpaşa" },
    { value: "Kiraz", label: "Kiraz" },
    { value: "Konak", label: "Konak" },
    { value: "Menderes", label: "Menderes" },
    { value: "Menemen", label: "Menemen" },
    { value: "Narlidere", label: "Narlıdere" },
    { value: "Odemis", label: "Ödemiş" },
    { value: "Seferihisar", label: "Seferihisar" },
    { value: "Selcuk", label: "Selçuk" },
    { value: "Tire", label: "Tire" },
    { value: "Torbali", label: "Torbalı" },
    { value: "Urla", label: "Urla" },
  ],
}

// ---------------------------------------------------------------------------
// Alt Kategoriler — mülk tipine göre
// ---------------------------------------------------------------------------

export interface SubCategoryData {
  value: string
  label: string
}

export type DetailedPropertyType = "daire" | "villa" | "ofis" | "arsa" | "dukkan"

export const subCategoriesByType: Record<DetailedPropertyType, SubCategoryData[]> = {
  daire: [
    { value: "normal", label: "Normal Daire" },
    { value: "studyo", label: "Stüdyo" },
    { value: "loft", label: "Loft" },
    { value: "dublex", label: "Dubleks" },
    { value: "penthouse", label: "Penthouse" },
    { value: "rezidans", label: "Rezidans" },
  ],
  villa: [
    { value: "mustakil", label: "Müstakil" },
    { value: "ikiz", label: "İkiz" },
    { value: "triplex", label: "Tripleks" },
    { value: "yazlik", label: "Yazlık" },
  ],
  ofis: [
    { value: "hazir", label: "Hazır Ofis" },
    { value: "acik", label: "Açık Ofis" },
    { value: "paylasimli", label: "Paylaşımlı Ofis" },
    { value: "geleneksel", label: "Geleneksel" },
  ],
  arsa: [
    { value: "konut", label: "Konut Arsası" },
    { value: "ticari", label: "Ticari Arsa" },
    { value: "tarla", label: "Tarla" },
    { value: "bahce", label: "Bahçe" },
  ],
  dukkan: [
    { value: "magaza", label: "Mağaza" },
    { value: "cadde", label: "Cadde Dükkanı" },
    { value: "avm", label: "AVM Dükkanı" },
    { value: "depo", label: "Depo" },
  ],
}

// ---------------------------------------------------------------------------
// Yardimci fonksiyonlar
// ---------------------------------------------------------------------------

/** Seçili ile göre ilçe listesini döndürür */
export function getDistrictsForCity(cityValue: string): DistrictData[] {
  return districtsByCity[cityValue] ?? []
}

/** Seçili mülk tipine göre alt kategori listesini döndürür */
export function getSubCategories(propertyType: DetailedPropertyType): SubCategoryData[] {
  return subCategoriesByType[propertyType] ?? []
}

/** Tüm ilçeleri düz liste olarak döndürür (farklı illerden) */
export function getAllDistricts(): DistrictData[] {
  return Object.values(districtsByCity).flat()
}
