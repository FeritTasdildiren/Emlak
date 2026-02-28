export type ShowcaseStatus = "active" | "draft";

export interface ShowcaseTheme {
  primary_color: string;
  background: "light" | "dark";
  layout: "grid" | "list";
}

export interface ShowcaseAgent {
  name: string;
  phone?: string;
  email?: string;
  photo_url?: string;
  office_name?: string;
}

export interface Showcase {
  id: string;
  title: string;
  slug: string;
  description?: string;
  is_active: boolean;
  views_count: number;
  selected_properties: string[];
  agent: ShowcaseAgent;
  theme: ShowcaseTheme;
  created_at: string;
  updated_at: string;
}
