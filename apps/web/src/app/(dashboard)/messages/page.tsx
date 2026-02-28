export default function MessagesPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Mesajlar</h1>
      <p className="text-gray-500">Müşterileriniz ve ekip arkadaşlarınızla iletişimde kalın.</p>
      <div className="border border-blue-200 bg-blue-50 rounded-lg p-8 flex flex-col items-center justify-center text-center min-h-[300px]">
        <div className="w-16 h-16 bg-blue-100 flex items-center justify-center rounded-full mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-600">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Yakında Geliyor</h2>
        <p className="text-gray-600 max-w-md">
          Müşterileriniz ve ekip arkadaşlarınızla doğrudan mesajlaşma özelliği yakında burada olacak.
        </p>
      </div>
    </div>
  );
}
