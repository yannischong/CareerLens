import { login, signup } from "./actions";


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
    <main className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow">
        <h1 className="mb-2 text-3xl font-bold">
          CareerCompass
        </h1>

        <p className="mb-6 text-gray-600">
          Sign in or create an account.
        </p>

        {params.error && (
          <div className="mb-4 rounded bg-red-50 p-3 text-sm text-red-700">
            {params.error}
          </div>
        )}

        <form className="space-y-4">
          <div>
            <label
              htmlFor="email"
              className="mb-1 block text-sm font-medium"
            >
              Email
            </label>

            <input
              id="email"
              name="email"
              type="email"
              required
              className="w-full rounded border px-3 py-2"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-1 block text-sm font-medium"
            >
              Password
            </label>

            <input
              id="password"
              name="password"
              type="password"
              required
              minLength={8}
              className="w-full rounded border px-3 py-2"
            />
          </div>

          <button
            formAction={login}
            className="w-full rounded bg-black px-4 py-2 text-white"
          >
            Sign in
          </button>

          <button
            formAction={signup}
            className="w-full rounded border px-4 py-2"
          >
            Create account
          </button>
        </form>
      </div>
    </main>
  );
}