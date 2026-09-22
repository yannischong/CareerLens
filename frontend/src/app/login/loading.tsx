export default function Loading() {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-blue-950 to-blue-800">
        <div className="flex flex-col items-center gap-4 text-white">
          <div className="h-9 w-9 animate-spin rounded-full border-4 border-blue-200 border-r-transparent" />
  
          <div className="text-center">
            <p className="font-medium">
              Loading CareerCompass
            </p>
  
            <p className="mt-1 text-sm text-blue-200">
              Getting things ready...
            </p>
          </div>
        </div>
      </main>
    );
  }