"use client";

import { Card } from "@/components/ui/card";
import { Users, Building2, Activity, Bell, FileCheck, Calendar, ChevronRight } from "lucide-react";
import { useProfile } from "@/hooks/use-profile";
import { useDashboard } from "@/hooks/use-dashboard";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDate } from "@/lib/utils";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";

export default function DashboardPage() {
  const { user, isLoading: userLoading } = useProfile();
  const { stats, isLoading: statsLoading } = useDashboard();

  const isLoading = userLoading || statsLoading;

  const currentTime = new Intl.DateTimeFormat("tr-TR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date());

  const dashboardStats = [
    {
      title: "Toplam Portföy",
      value: stats?.portfolio_count ?? 0,
      description: `${stats?.active_portfolio_count ?? 0} aktif ilan`,
      icon: Building2,
      color: "text-blue-600",
      bg: "bg-blue-100",
    },
    {
      title: "Toplam Müşteri",
      value: stats?.customer_count ?? 0,
      description: "Tüm müşteri veritabanı",
      icon: Users,
      color: "text-green-600",
      bg: "bg-green-100",
    },
    {
      title: "Bu Ayki Değerleme",
      value: stats?.valuation_count_this_month ?? 0,
      description: "Hazırlanan rapor sayısı",
      icon: FileCheck,
      color: "text-purple-600",
      bg: "bg-purple-100",
    },
    {
      title: "Okunmamış Bildirim",
      value: stats?.unread_notification_count ?? 0,
      description: "Yeni güncellemeler",
      icon: Bell,
      color: "text-orange-600",
      bg: "bg-orange-100",
    },
  ];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-4 w-48" />
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="p-6 flex items-center justify-between">
              <div className="space-y-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-8 w-16" />
                <Skeleton className="h-3 w-32" />
              </div>
              <Skeleton className="h-12 w-12 rounded-full" />
            </Card>
          ))}
        </div>

        <div className="grid gap-6 grid-cols-1 lg:grid-cols-7">
          <Card className="lg:col-span-4 p-6">
            <Skeleton className="h-6 w-32 mb-4" />
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex gap-4 p-3 items-center">
                  <Skeleton className="h-10 w-10 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-3 w-2/3" />
                  </div>
                </div>
              ))}
            </div>
          </Card>
          <Card className="lg:col-span-3 p-6">
            <Skeleton className="h-6 w-32 mb-4" />
            <Skeleton className="h-48 w-full" />
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">
          Hoş Geldiniz, {user?.full_name?.split(" ")[0]}
        </h1>
        <span className="text-sm text-gray-500">
          Son güncelleme: {currentTime}
        </span>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {dashboardStats.map((stat) => (
          <Card key={stat.title} className="p-6 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">{stat.title}</p>
              <h3 className="text-2xl font-bold mt-1">{stat.value}</h3>
              <p className="text-xs text-gray-500 mt-1">{stat.description}</p>
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
          {stats?.recent_activities && stats.recent_activities.length > 0 ? (
            <div className="space-y-4">
              {stats.recent_activities.map((activity) => (
                <div key={activity.id} className="flex gap-4 p-3 hover:bg-gray-50 rounded-lg transition-colors items-start">
                  <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center text-gray-600 flex-shrink-0">
                    <Activity className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="font-medium text-sm text-gray-900">{activity.title}</p>
                    <p className="text-sm text-gray-500">{activity.description}</p>
                    <p className="text-xs text-gray-400 mt-1">
                      {formatDate(activity.created_at)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-[200px] flex items-center justify-center border-2 border-dashed border-gray-200 rounded-lg bg-gray-50 text-gray-400">
              Henüz aktivite bulunmuyor.
            </div>
          )}
        </Card>
        <Card className="lg:col-span-3 p-6 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold">Yaklaşan Randevular</h3>
            <Link 
              href="/dashboard/appointments" 
              className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
            >
              Tümünü Gör
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          
          {stats?.upcoming_appointments && stats.upcoming_appointments.length > 0 ? (
            <div className="space-y-4 flex-1">
              {stats.upcoming_appointments.map((appointment) => (
                <div key={appointment.id} className="flex gap-3 p-3 bg-gray-50 rounded-lg items-center">
                  <div className="w-10 h-10 bg-white rounded-md border flex flex-col items-center justify-center text-gray-600 flex-shrink-0">
                    <Calendar className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-sm text-gray-900 truncate">
                      {appointment.title}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <p className="text-xs text-gray-500">
                        {new Date(appointment.appointment_date).toLocaleDateString("tr-TR", {
                          day: "numeric",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                      {appointment.customer_name && (
                        <>
                          <span className="text-gray-300">•</span>
                          <p className="text-xs text-gray-600 truncate">
                            {appointment.customer_name}
                          </p>
                        </>
                      )}
                    </div>
                  </div>
                  <Badge 
                    variant={
                      appointment.status === "scheduled" ? "default" : 
                      appointment.status === "completed" ? "success" : 
                      appointment.status === "cancelled" ? "destructive" : "secondary"
                    }
                    className="text-[10px] px-1.5 h-5"
                  >
                    {appointment.status === "scheduled" ? "Planlandı" : 
                     appointment.status === "completed" ? "Tamamlandı" : 
                     appointment.status === "cancelled" ? "İptal" : "Gelmedi"}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-gray-200 rounded-lg bg-gray-50 text-gray-400 text-center p-4">
              <Calendar className="w-8 h-8 mb-2 opacity-50" />
              <p className="text-sm font-medium">Henüz randevu bulunmuyor.</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
