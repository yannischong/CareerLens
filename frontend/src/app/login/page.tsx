import AuthForm from "./auth-form";


type LoginPageProps = {
  searchParams: Promise<{
    error?: string;
  }>;
};


export default async function LoginPage({
  searchParams,
}: LoginPageProps) {
  const params = await searchParams;

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-blue-950 to-blue-800 px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center text-white">
          <p className="mb-2 text-sm font-medium uppercase tracking-[0.2em] text-blue-200">
            Search smarter. Tailor faster.
          </p>

          <h1 className="text-4xl font-bold tracking-tight">
            CareerCompass
          </h1>

          <p className="mt-3 text-sm text-blue-100">
            Stop guessing what companies look for in
            your resume.
          </p>
        </div>

        <AuthForm serverError={params.error} />
      </div>
    </main>
  );
}