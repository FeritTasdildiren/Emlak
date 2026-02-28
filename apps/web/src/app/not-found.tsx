import Link from 'next/link';
import { FileQuestion } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center p-4 text-center bg-gray-50/50">
      <div className="rounded-full bg-white p-4 mb-6 shadow-sm border border-gray-100">
        <FileQuestion className="h-10 w-10 text-gray-400" />
      </div>
      <h2 className="text-2xl font-bold tracking-tight text-gray-900 mb-2">Sayfa Bulunamadı</h2>
      <p className="text-gray-600 mb-8 max-w-md mx-auto">
        Aradığınız sayfaya ulaşılamıyor. Adres değişmiş olabilir veya sayfa yayından kaldırılmış olabilir.
      </p>
      <Link
        href="/"
        className="inline-flex items-center justify-center rounded-md bg-blue-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
      >
        Ana Sayfaya Dön
      </Link>
    </div>
  );
}
