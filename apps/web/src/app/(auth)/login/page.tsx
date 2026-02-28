import type { Metadata } from "next";
import Link from "next/link";
import { LoginForm } from "./login-form";

export const metadata: Metadata = {
  title: "Giriş Yap",
  description: "Emlak Platform hesabınıza giriş yapın.",
};

export default function LoginPage() {
  return (
    <div>
      <h2 className="mt-2 text-center text-2xl font-bold leading-9 tracking-tight text-gray-900">
        Hesabınıza giriş yapın
      </h2>
      <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-sm">
        <LoginForm />

        <p className="mt-10 text-center text-sm text-gray-500">
          Hesabınız yok mu?{" "}
          <Link href="/register" className="font-semibold leading-6 text-blue-600 hover:text-blue-500">
            Ücretsiz kayıt olun
          </Link>
        </p>
      </div>
    </div>
  );
}
