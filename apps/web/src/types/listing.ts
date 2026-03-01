export type PropertyType = 'daire' | 'villa' | 'ofis' | 'arsa' | 'dukkan';
export type RoomCount = '1+0' | '1+1' | '2+0' | '2+1' | '2+2' | '3+0' | '3+1' | '3+2' | '4+1' | '4+2' | '5+1' | '5+2' | '6+1' | '6+2' | '7+';
export type BathroomCount = '1' | '2' | '3' | '4' | '5+';
export type FloorInfo = 'bodrum' | 'zemin_kat' | 'giris_kat' | 'ara_kat' | 'en_ust_kat' | 'dublex' | 'triplex' | 'cati_kati';
export type HeatingType = 'dogalgaz_kombi' | 'dogalgaz_merkezi' | 'merkezi_pay_olcer' | 'klima' | 'soba' | 'yerden_isitma' | 'yok';
export type FurnitureStatus = 'bos' | 'esyali' | 'yari_esyali';
export type Facade = 'kuzey' | 'guney' | 'dogu' | 'bati' | 'kuzey_dogu' | 'kuzey_bati' | 'guney_dogu' | 'guney_bati';
export type ToneType = 'kurumsal' | 'samimi' | 'acil';
export type PortalType = 'sahibinden' | 'hepsiemlak' | 'both';

export interface PropertyFeatures {
  balcony: boolean;
  parking: boolean;
  security: boolean;
  pool: boolean;
  seaView: boolean;
  centralHeating: boolean;
  elevator: boolean;
  metroNearby: boolean;
  [key: string]: boolean;
}

export interface ListingFormData {
  property_id?: string;
  propertyType: PropertyType;
  subCategory?: string;
  roomCount?: RoomCount;
  bathroomCount?: BathroomCount;
  grossSqm: number;
  netSqm?: number;
  price: number;
  floor?: number;
  totalFloors?: number;
  buildingAge?: number;
  floorInfo?: FloorInfo;
  heatingType?: HeatingType;
  furnitureStatus?: FurnitureStatus;
  facade?: Facade;
  city: string;
  district: string;
  neighborhood?: string;
  features: PropertyFeatures;
  additionalNotes: string;
  tone: ToneType;
}

export interface GeneratedListing {
  title: string;
  description: string; // markdown
  tone: ToneType;
  generatedAt: string; // ISO date
  wordCount: number;
  highlights: string[];
  seoKeywords: string[];
}

export interface ListingTextRequest {
  formData: ListingFormData;
}

export interface ListingTextResponse {
  success: boolean;
  data: GeneratedListing;
  creditsUsed: number;
  creditsRemaining: number;
}

export interface ToneInfo {
  id: ToneType;
  label: string;
  description: string;
  iconName: 'building' | 'heart' | 'flame';
}

// Virtual Staging Types

export type StagingStyle = 'modern' | 'klasik' | 'minimalist' | 'skandinav' | 'bohem' | 'endustriyel';

export interface StyleInfo {
  id: StagingStyle;
  label: string;
  description: string;
  imageUrl: string;
}

export interface RoomAnalysis {
  roomType: string;
  detectedObjects: string[];
  lighting: string;
}

export interface StagingRequest {
  imageFile: File;
  style: StagingStyle;
  instructions?: string;
}

export interface StagingResponse {
  originalImageUrl: string;
  stagedImageUrl: string;
  analysis: RoomAnalysis;
  creditsUsed: number;
}

// Portal Export Types

export interface PortalExportRequest {
  listingId?: string; // If saving from DB
  generatedText: GeneratedListing;
  portals: PortalType[];
}

export interface PortalExportResponse {
  success: boolean;
  exportUrl?: string; // URL to download zip or html
  portalPreview: {
    portal: PortalType;
    formattedContent: string;
  }[];
}
