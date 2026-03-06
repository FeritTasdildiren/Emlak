"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/toast";
import { CustomerForm, CustomerFormValues } from "@/components/customers/customer-form";
import { useCreateCustomer } from "@/hooks/use-customers";
import type { Customer } from "@/types/customer";

export default function NewCustomerPage() {
  const router = useRouter();
  const createCustomer = useCreateCustomer();

  const handleSubmit = async (data: CustomerFormValues) => {
    try {
      await createCustomer.mutateAsync(data as unknown as Partial<Customer>);
      toast("Müşteri başarıyla oluşturuldu", "success");
      router.push("/dashboard/customers");
    } catch (err: unknown) {
      const error = err as { detail?: string; message?: string };
      toast(error?.detail || error?.message || "Müşteri oluşturulamadı", "error");
    }
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 w-full max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard/customers">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Yeni Müşteri</h1>
          <p className="mt-1 text-sm text-gray-500">
            Portföyünüze yeni bir müşteri ekleyin.
          </p>
        </div>
      </div>

      {/* Form */}
      <CustomerForm onSubmit={handleSubmit} isLoading={createCustomer.isPending} />
    </div>
  );
}
