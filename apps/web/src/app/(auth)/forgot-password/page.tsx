import type { Metadata } from "next";
import Link from "next/link";
import { ForgotPasswordForm } from "./forgot-password-form";

export const metadata: Metadata = {
  title: "Şifremi Unuttum",
  description: "Şifre sıfırlama linki talep edin.",
};

export default function ForgotPasswordPage() {
  return (
    <div>
      <h2 className="mt-2 text-center text-2xl font-bold leading-9 tracking-tight text-gray-900">
        Şifrenizi mi unuttunuz?
      </h2>
      <p className="mt-2 text-center text-sm text-gray-600">
        E-posta adresinizi girin, size şifre sıfırlama linki gönderelim.
      </p>
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-sm">
        <ForgotPasswordForm />

        <p className="mt-10 text-center text-sm text-gray-500">
          Şifrenizi hatırladınız mı?{" "}
          <Link
            href="/login"
            className="font-semibold leading-6 text-blue-600 hover:text-blue-500"
          >
            Giriş yapın
          </Link>
        </p>
      </div>
    </div>
  );
}
