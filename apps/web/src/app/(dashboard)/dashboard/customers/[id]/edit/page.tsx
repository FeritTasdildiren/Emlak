"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/toast";
import { CustomerForm, CustomerFormValues } from "@/components/customers/customer-form";
import { useCustomerDetail, useUpdateCustomer } from "@/hooks/use-customers";
import type { Customer } from "@/types/customer";

export default function EditCustomerPage() {
  const params = useParams();
  const id = params.id as string;
  const router = useRouter();

  const { data: customer, isLoading: isLoadingCustomer } = useCustomerDetail(id);
  const updateCustomer = useUpdateCustomer();

  const handleEditSubmit = async (data: CustomerFormValues) => {
    try {
      await updateCustomer.mutateAsync({ id, data: data as unknown as Partial<Customer> });
      toast("Müşteri başarıyla güncellendi", "success");
      router.push(`/dashboard/customers/${id}`);
    } catch (err: unknown) {
      const error = err as { detail?: string; message?: string };
      toast(error?.detail || error?.message || "Müşteri güncellenemedi", "error");
    }
  };

  if (isLoadingCustomer) {
    return (
      <div className="flex h-[60vh] w-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!customer) {
    return (
      <div className="px-4 py-12 text-center">
        <h2 className="text-xl font-semibold text-gray-900">Müşteri bulunamadı</h2>
        <p className="mt-2 text-gray-500">
          Düzenlemek istediğiniz müşteri kaydı mevcut değil.
        </p>
        <Link href="/dashboard/customers" className="mt-6 inline-block">
          <Button variant="outline">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Müşterilere Dön
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 w-full max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href={`/dashboard/customers/${id}`}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Müşteriyi Düzenle</h1>
          <p className="mt-1 text-sm text-gray-500">
            {customer.full_name} isimli müşterinin bilgilerini güncelleyin.
          </p>
        </div>
      </div>

      {/* Form */}
      <CustomerForm
        isEditing={true}
        defaultValues={{
          ...customer,
          desired_districts: customer.desired_districts ?? [],
          tags: customer.tags ?? [],
        }}
        onSubmit={handleEditSubmit}
        isLoading={updateCustomer.isPending}
      />
    </div>
  );
}
