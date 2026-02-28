import { Metadata } from "next";
import { notFound } from "next/navigation";
import {
  fetchShowcaseBySlug,
  incrementShowcaseViews,
} from "@/lib/api/showcases";
import { Avatar } from "@/components/ui/avatar";
import { Phone, Mail, Building2, MapPin, Ruler } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import type { Property } from "@/types/property";

interface ShowcasePageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata(
  props: ShowcasePageProps
): Promise<Metadata> {
  const params = await props.params;
  const showcase = await fetchShowcaseBySlug(params.slug);

  if (!showcase) {
    return {
      title: "Vitrin Bulunamadı",
      description: "Aradığınız vitrin sayfası bulunamadı veya yayından kaldırılmış olabilir.",
    };
  }

  const title = `${showcase.title} | ${showcase.agent.name}`;
  const description = showcase.description || `${showcase.agent.name} tarafından sizin için özel hazırlanmış ilan seçkisi.`;

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      type: "website",
      images: showcase.agent.photo_url ? [showcase.agent.photo_url] : [],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: showcase.agent.photo_url ? [showcase.agent.photo_url] : [],
    },
  };
}

export default async function ShowcasePage(props: ShowcasePageProps) {
  const params = await props.params;
  const showcase = await fetchShowcaseBySlug(params.slug);

  if (!showcase || !showcase.is_active) {
    notFound();
  }

  // Increment views
  await incrementShowcaseViews(showcase.slug);

  const themeColors = {
    primary: showcase.theme.primary_color || "#ea580c",
  };

  const whatsappMessage = encodeURIComponent(
    `Merhaba ${showcase.agent.name}, "${showcase.title}" vitrininizi inceledim, ilanlar hakkında bilgi almak istiyorum.`
  );
  
  // Format phone for WhatsApp link (+90 532 123 4567 -> 905321234567)
  const phoneDigits = showcase.agent.phone?.replace(/\D/g, "") || "";
  const whatsappUrl = `https://wa.me/${phoneDigits}?text=${whatsappMessage}`;

  return (
    <div className={cn("min-h-screen", showcase.theme.background === "dark" ? "bg-gray-900 text-white" : "bg-gray-50 text-gray-900")}>
      <header className="bg-white shadow-sm sticky top-0 z-40" style={showcase.theme.background === "dark" ? { backgroundColor: "#1f2937", borderBottom: "1px solid #374151" } : {}}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <Avatar
                fallback={showcase.agent.name}
                src={showcase.agent.photo_url}
                className="h-16 w-16 text-xl"
              />
              <div>
                <h1 className="text-xl font-bold" style={{ color: themeColors.primary }}>
                  {showcase.agent.name}
                </h1>
                <p className="text-sm text-gray-500 flex items-center gap-1 mt-1" style={showcase.theme.background === "dark" ? { color: "#9ca3af" } : {}}>
                  <Building2 className="h-4 w-4" />
                  {showcase.agent.office_name || "Gayrimenkul Danışmanı"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4 text-sm font-medium">
              {showcase.agent.phone && (
                <a
                  href={`tel:${showcase.agent.phone.replace(/\s+/g, "")}`}
                  className="flex items-center gap-2 hover:opacity-80 transition-opacity px-4 py-2 rounded-lg bg-gray-100"
                  style={showcase.theme.background === "dark" ? { backgroundColor: "#374151", color: "#f3f4f6" } : {}}
                >
                  <Phone className="h-4 w-4" style={{ color: themeColors.primary }} />
                  {showcase.agent.phone}
                </a>
              )}
              {showcase.agent.email && (
                <a
                  href={`mailto:${showcase.agent.email}`}
                  className="hidden sm:flex items-center gap-2 hover:opacity-80 transition-opacity px-4 py-2 rounded-lg bg-gray-100"
                  style={showcase.theme.background === "dark" ? { backgroundColor: "#374151", color: "#f3f4f6" } : {}}
                >
                  <Mail className="h-4 w-4" style={{ color: themeColors.primary }} />
                  E-posta
                </a>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12 pb-24">
        <div className="mb-10 text-center max-w-3xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-extrabold mb-4">
            {showcase.title}
          </h2>
          {showcase.description && (
            <p className="text-lg text-gray-600 leading-relaxed" style={showcase.theme.background === "dark" ? { color: "#d1d5db" } : {}}>
              {showcase.description}
            </p>
          )}
        </div>

        <div className={cn(
          "grid gap-6",
          showcase.theme.layout === "list" 
            ? "grid-cols-1 max-w-4xl mx-auto" 
            : "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3"
        )}>
          {showcase.properties.map((property: Property) => (
            <div key={property.id} className="h-full">
              {/* Custom render to match public view specs over dashboard view */}
              <div className="h-full group rounded-xl border bg-white overflow-hidden shadow-sm hover:shadow-lg transition-all flex flex-col" style={showcase.theme.background === "dark" ? { backgroundColor: "#1f2937", borderColor: "#374151" } : {}}>
                {/* Image Placeholder */}
                <div className="aspect-[4/3] bg-gray-200 relative overflow-hidden flex items-center justify-center">
                  <span className="text-gray-400 font-medium tracking-widest uppercase">Görsel Yok</span>
                  <div className="absolute top-3 right-3 bg-white/90 backdrop-blur text-xs font-bold px-3 py-1.5 rounded-full shadow-sm" style={{ color: themeColors.primary }}>
                    {property.listing_type === "satilik" ? "SATILIK" : "KİRALIK"}
                  </div>
                </div>
                
                <div className="p-5 flex flex-col flex-grow">
                  <h3 className="font-semibold text-lg line-clamp-2 mb-2 group-hover:text-blue-600 transition-colors" style={showcase.theme.background === "dark" ? { color: "#f9fafb" } : {}}>
                    {property.title}
                  </h3>
                  
                  <div className="flex items-center gap-1.5 text-sm text-gray-500 mb-4" style={showcase.theme.background === "dark" ? { color: "#9ca3af" } : {}}>
                    <MapPin className="h-4 w-4 shrink-0" />
                    <span className="truncate">{property.district}, {property.city}</span>
                  </div>

                  <div className="mt-auto pt-4 border-t flex items-end justify-between" style={showcase.theme.background === "dark" ? { borderColor: "#374151" } : {}}>
                    <div className="flex flex-col gap-1">
                      <div className="text-xs text-gray-500 font-medium uppercase tracking-wider" style={showcase.theme.background === "dark" ? { color: "#9ca3af" } : {}}>Fiyat</div>
                      <div className="font-bold text-xl text-gray-900" style={showcase.theme.background === "dark" ? { color: "#f3f4f6" } : {}}>
                        {formatCurrency(property.price)}
                        {property.listing_type === "kiralik" && <span className="text-sm font-normal text-gray-500">/ay</span>}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3 text-sm font-medium text-gray-700 bg-gray-50 px-3 py-1.5 rounded-lg" style={showcase.theme.background === "dark" ? { backgroundColor: "#374151", color: "#d1d5db" } : {}}>
                      <div className="flex items-center gap-1.5">
                        <Ruler className="h-4 w-4 text-gray-400" />
                        <span>{property.area_sqm}m²</span>
                      </div>
                      {property.room_count && (
                        <>
                          <div className="w-1 h-1 rounded-full bg-gray-300" />
                          <span>{property.room_count} Oda</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>

      {/* Sticky WhatsApp Bar */}
      {showcase.agent.phone && (
        <div className="fixed bottom-0 left-0 right-0 p-4 bg-white/80 backdrop-blur-md border-t shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-50" style={showcase.theme.background === "dark" ? { backgroundColor: "rgba(31, 41, 55, 0.9)", borderColor: "#374151" } : {}}>
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="hidden sm:block">
              <p className="font-medium text-gray-900" style={showcase.theme.background === "dark" ? { color: "#f3f4f6" } : {}}>
                Bu ilanlarla ilgileniyor musunuz?
              </p>
              <p className="text-sm text-gray-500" style={showcase.theme.background === "dark" ? { color: "#9ca3af" } : {}}>
                Hemen iletişime geçin, detayları görüşelim.
              </p>
            </div>
            <a
              href={whatsappUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full sm:w-auto flex items-center justify-center gap-2 bg-[#25D366] hover:bg-[#128C7E] text-white font-medium px-6 py-3 rounded-xl transition-colors shadow-sm"
            >
              <svg viewBox="0 0 24 24" className="w-6 h-6 fill-current">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51a12.8 12.8 0 0 0-.57-.01c-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z"/>
              </svg>
              WhatsApp ile İletişime Geç
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
