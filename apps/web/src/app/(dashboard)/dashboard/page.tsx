import { Card } from "@/components/ui/card";
import { Users, Building2, TrendingUp, Activity } from "lucide-react";

const stats = [
  {
    title: "Toplam Portföy",
    value: "24",
    change: "+2 bu ay",
    icon: Building2,
    color: "text-blue-600",
    bg: "bg-blue-100",
  },
  {
    title: "Aktif Müşteriler",
    value: "156",
    change: "+12 bu ay",
    icon: Users,
    color: "text-green-600",
    bg: "bg-green-100",
  },
  {
    title: "Tahmini Değer",
    value: "₺42.5M",
    change: "%5 artış",
    icon: TrendingUp,
    color: "text-purple-600",
    bg: "bg-purple-100",
  },
  {
    title: "Bekleyen İşler",
    value: "7",
    change: "3 acil",
    icon: Activity,
    color: "text-orange-600",
    bg: "bg-orange-100",
  },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">
          Hoş Geldiniz, John
        </h1>
        <span className="text-sm text-gray-500">Son güncelleme: Bugün 09:41</span>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title} className="p-6 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">{stat.title}</p>
              <h3 className="text-2xl font-bold mt-1">{stat.value}</h3>
              <p className="text-xs text-gray-500 mt-1">{stat.change}</p>
            </div>
            <div className={`p-3 rounded-full ${stat.bg}`}>
              <stat.icon className={`w-6 h-6 ${stat.color}`} />
            </div>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 grid-cols-1 lg:grid-cols-7">
        <Card className="lg:col-span-4 p-6">
          <h3 className="text-lg font-bold mb-4">Son Aktiviteler</h3>
          <div className="h-[200px] flex items-center justify-center border-2 border-dashed border-gray-200 rounded-lg bg-gray-50 text-gray-400">
            Grafik Placeholder
          </div>
        </Card>
        <Card className="lg:col-span-3 p-6">
          <h3 className="text-lg font-bold mb-4">Yaklaşan Randevular</h3>
           <div className="space-y-4">
             {[1, 2, 3].map((i) => (
               <div key={i} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                 <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold">
                   1{i}
                 </div>
                 <div>
                   <p className="font-medium text-sm">Müşteri Görüşmesi</p>
                   <p className="text-xs text-gray-500">14:00 - Ofis</p>
                 </div>
               </div>
             ))}
           </div>
        </Card>
      </div>
    </div>
  );
}
