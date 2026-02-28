import type { Metadata } from "next";
import { Suspense } from "react";
import { ResetPasswordForm } from "./reset-password-form";

export const metadata: Metadata = {
  title: "Şifre Sıfırla",
  description: "Yeni şifrenizi belirleyin.",
};

export default function ResetPasswordPage() {
  return (
    <div>
      <h2 className="mt-2 text-center text-2xl font-bold leading-9 tracking-tight text-gray-900">
        Yeni şifrenizi belirleyin
      </h2>
      <p className="mt-2 text-center text-sm text-gray-600">
        Lütfen yeni şifrenizi girin.
      </p>
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-sm">
        <Suspense fallback={<div className="text-center text-sm text-gray-500">Yükleniyor...</div>}>
          <ResetPasswordForm />
        </Suspense>
      </div>
    </div>
  );
}
