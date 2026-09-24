import {
  LoadingSpinner,
} from "./loading-spinner";


export default function Loading() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-950">
      <div className="flex max-w-md flex-col items-center rounded-2xl border border-slate-200 bg-white px-8 py-10 text-center shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <LoadingSpinner
          className="h-9 w-9 text-[#0A66C2]"
          label="Loading CareerCompass"
        />

        <p className="mt-4 font-semibold text-slate-900 dark:text-white">
          Loading CareerCompass...
        </p>

        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Getting your workspace ready. This can take a little longer after a period of inactivity.
        </p>

        <p className="mt-3 text-xs font-medium text-slate-400 dark:text-slate-500">
          Estimated time for initial startup: 15 seconds
        </p>
      </div>
    </main>
  );
}
