import { Settings, Construction } from "lucide-react";

export default function TgSettingsPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4 space-y-6">
      <div className="relative">
        <div className="bg-gray-100 p-6 rounded-full">
          <Settings className="w-12 h-12 text-gray-400" />
        </div>
        <div className="absolute -bottom-1 -right-1 bg-amber-100 p-1.5 rounded-full">
          <Construction className="w-4 h-4 text-amber-600" />
        </div>
      </div>
      <div className="space-y-2 max-w-sm">
        <h2 className="text-xl font-bold text-gray-900">Ayarlar</h2>
        <p className="text-gray-500 text-sm">
          Bu sayfa yakında kullanıma sunulacaktır. Bildirim tercihleri, profil
          ayarları ve uygulama konfigürasyonu burada yer alacak.
        </p>
      </div>
      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
        Yakında
      </span>
    </div>
  );
}
