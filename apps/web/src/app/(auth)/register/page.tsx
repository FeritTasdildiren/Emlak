import type { Metadata } from "next";
import Link from "next/link";
import { RegisterForm } from "./register-form";

export const metadata: Metadata = {
  title: "Kayıt Ol",
  description: "Emlak Platform'a ücretsiz kayıt olun ve işinizi yönetmeye başlayın.",
};

export default function RegisterPage() {
  return (
    <div>
      <h2 className="mt-2 text-center text-2xl font-bold leading-9 tracking-tight text-gray-900">
        Yeni hesap oluşturun
      </h2>
      <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-sm">
        <RegisterForm />

        <p className="mt-10 text-center text-sm text-gray-500">
          Zaten hesabınız var mı?{" "}
          <Link href="/login" className="font-semibold leading-6 text-blue-600 hover:text-blue-500">
            Giriş yapın
          </Link>
        </p>
      </div>
    </div>
  );
}
