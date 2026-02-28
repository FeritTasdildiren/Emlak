// Eşleştirme (Match) type tanımları
// Müşteri-ilan uyum eşleştirmelerini temsil eder

export type MatchStatus =
  | "pending"
  | "interested"
  | "passed"
  | "contacted"
  | "converted";

/** Uyum skoru detayları — notes JSON alanında saklanır */
export interface MatchScoreDetails {
  price_score: number; // 0-100 fiyat uyumu
  location_score: number; // 0-100 konum uyumu
  room_score: number; // 0-100 oda uyumu
  area_score: number; // 0-100 alan uyumu
}

/** Eşleşme kartında gösterilecek ilan özet bilgisi */
export interface MatchProperty {
  title: string;
  price: number;
  district: string;
  rooms: string;
}

/** Tam eşleştirme kaydı */
export interface Match {
  id: string;
  property_id: string;
  customer_id: string;
  score: number; // 0-100 genel uyum skoru
  status: MatchStatus;
  matched_at: string; // ISO date string
  responded_at?: string; // ISO date string
  notes: string; // JSON string of MatchScoreDetails
  property?: MatchProperty;
}
