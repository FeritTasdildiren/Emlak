"use client";

import { useState } from "react";
import { Plus, Calendar, Clock, MapPin, Edit2, Trash2, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  useAppointments, 
  useCreateAppointment, 
  useUpdateAppointment, 
  useDeleteAppointment 
} from "@/hooks/use-appointments";
import { Modal } from "@/components/ui/modal";
import { AppointmentForm, AppointmentFormValues } from "@/components/appointment-form";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Appointment, AppointmentFormData } from "@/types/appointment";
import { cn } from "@/lib/utils";
import { toast } from "@/components/ui/toast";

const STATUS_OPTIONS = [
  { value: "all", label: "Tümü" },
  { value: "scheduled", label: "Planlandı" },
  { value: "completed", label: "Tamamlandı" },
  { value: "cancelled", label: "İptal" },
  { value: "no_show", label: "Gelmedi" },
];

export default function AppointmentsPage() {
  const [statusFilter, setStatusFilter] = useState("all");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAppointment, setEditingAppointment] = useState<Appointment | null>(null);
  const [deletingAppointmentId, setDeletingAppointmentId] = useState<string | null>(null);

  const { data, isLoading, isError } = useAppointments({
    status: statusFilter === "all" ? undefined : statusFilter,
  });

  const createMutation = useCreateAppointment();
  const updateMutation = useUpdateAppointment(editingAppointment?.id || "");
  const deleteMutation = useDeleteAppointment();

  const handleCreateOrUpdate = async (values: AppointmentFormValues) => {
    try {
      const payload: AppointmentFormData = {
        ...values,
        duration_minutes: parseInt(values.duration_minutes, 10),
        description: values.description || undefined,
        location: values.location || undefined,
        notes: values.notes || undefined,
        customer_id: values.customer_id || undefined,
        property_id: values.property_id || undefined,
      };

      if (editingAppointment) {
        await updateMutation.mutateAsync(payload);
        toast("Randevu güncellendi.", "success");
      } else {
        await createMutation.mutateAsync(payload);
        toast("Yeni randevu oluşturuldu.", "success");
      }
      setIsModalOpen(false);
      setEditingAppointment(null);
    } catch (err) {
      console.error(err);
      toast("İşlem sırasında bir hata oluştu.", "error");
    }
  };

  const handleDelete = async () => {
    if (!deletingAppointmentId) return;
    try {
      await deleteMutation.mutateAsync(deletingAppointmentId);
      toast("Randevu silindi.", "success");
      setDeletingAppointmentId(null);
    } catch (err) {
      console.error(err);
      toast("Silme işlemi başarısız oldu.", "error");
    }
  };

  const openEditModal = (appointment: Appointment) => {
    setEditingAppointment(appointment);
    setIsModalOpen(true);
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 w-full max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Randevular</h1>
          <p className="text-sm text-gray-500 mt-1">
            Tüm randevularınızı buradan yönetebilirsiniz.
          </p>
        </div>
        <Button onClick={() => { setEditingAppointment(null); setIsModalOpen(true); }}>
          <Plus className="w-4 h-4 mr-2" />
          Yeni Randevu
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide">
        <Filter className="w-4 h-4 text-gray-400 mr-2 shrink-0" />
        {STATUS_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setStatusFilter(opt.value)}
            className={cn(
              "px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors",
              statusFilter === opt.value
                ? "bg-blue-600 text-white shadow-sm"
                : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* List */}
      <div className="space-y-4">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <Card key={i} className="p-6">
              <div className="flex items-center justify-between gap-4">
                <div className="space-y-2 flex-1">
                  <Skeleton className="h-5 w-48" />
                  <Skeleton className="h-4 w-32" />
                </div>
                <Skeleton className="h-10 w-24 rounded-full" />
              </div>
            </Card>
          ))
        ) : isError ? (
          <div className="text-center py-12 bg-white rounded-xl border border-dashed">
            <p className="text-red-500">Randevular yüklenirken bir hata oluştu.</p>
          </div>
        ) : data?.items && data.items.length > 0 ? (
          <div className="grid gap-4">
            {data.items.map((appointment) => (
              <Card key={appointment.id} className="p-4 sm:p-6 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex gap-4">
                    <div className="hidden sm:flex w-12 h-12 bg-blue-50 text-blue-600 rounded-lg flex-col items-center justify-center border border-blue-100">
                      <Calendar className="w-6 h-6" />
                    </div>
                    <div>
                      <h4 className="font-bold text-gray-900">{appointment.title}</h4>
                      <div className="flex flex-wrap items-center gap-y-1 gap-x-4 mt-1 text-sm text-gray-500">
                        <div className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          {new Date(appointment.appointment_date).toLocaleDateString("tr-TR", {
                            day: "numeric",
                            month: "long",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                          {" "}({appointment.duration_minutes} dk)
                        </div>
                        {appointment.location && (
                          <div className="flex items-center gap-1">
                            <MapPin className="w-3.5 h-3.5" />
                            {appointment.location}
                          </div>
                        )}
                        {appointment.customer_name && (
                          <div className="flex items-center gap-1">
                            <Calendar className="w-3.5 h-3.5" />
                            {appointment.customer_name}
                          </div>
                        )}
                      </div>
                      {appointment.description && (
                        <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                          {appointment.description}
                        </p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <Badge 
                      variant={
                        appointment.status === "scheduled" ? "default" : 
                        appointment.status === "completed" ? "success" : 
                        appointment.status === "cancelled" ? "destructive" : "secondary"
                      }
                    >
                      {appointment.status === "scheduled" ? "Planlandı" : 
                       appointment.status === "completed" ? "Tamamlandı" : 
                       appointment.status === "cancelled" ? "İptal" : "Gelmedi"}
                    </Badge>
                    
                    <div className="flex items-center border-l pl-3 ml-1">
                      <button 
                        onClick={() => openEditModal(appointment)}
                        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={() => setDeletingAppointmentId(appointment.id)}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-center py-20 bg-white rounded-xl border-2 border-dashed border-gray-200">
            <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">Randevu bulunamadı</h3>
            <p className="text-gray-500 max-w-xs mx-auto mt-1">
              {statusFilter === "all" 
                ? "Henüz hiç randevu oluşturmamışsınız." 
                : "Bu kriterlere uygun randevu bulunmuyor."}
            </p>
            <Button 
              variant="outline" 
              className="mt-6"
              onClick={() => setIsModalOpen(true)}
            >
              <Plus className="w-4 h-4 mr-2" />
              İlk Randevuyu Oluştur
            </Button>
          </div>
        )}
      </div>

      {/* Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); setEditingAppointment(null); }}
        title={editingAppointment ? "Randevuyu Düzenle" : "Yeni Randevu Oluştur"}
      >
        <AppointmentForm 
          isEditing={!!editingAppointment}
          defaultValues={editingAppointment || undefined}
          onSubmit={handleCreateOrUpdate}
          isLoading={createMutation.isPending || updateMutation.isPending}
        />
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!deletingAppointmentId}
        variant="danger"
        title="Randevuyu Sil"
        description="Bu randevuyu silmek istediğinizden emin misiniz? Bu işlem geri alınamaz."
        confirmLabel="Sil"
        loading={deleteMutation.isPending}
        onConfirm={handleDelete}
        onCancel={() => setDeletingAppointmentId(null)}
      />
    </div>
  );
}
