import Link from "next/link";


function LockIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      className="h-4 w-4"
    >
      <path
        d="M7 10V8a5 5 0 0 1 10 0v2"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <rect
        x="5"
        y="10"
        width="14"
        height="10"
        rx="2"
        stroke="currentColor"
        strokeWidth="1.8"
      />
    </svg>
  );
}


export default function GuestDashboard() {
  return (
    <main className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">

      <section
        className="relative left-1/2 flex min-h-screen w-screen -translate-x-1/2 items-center overflow-hidden bg-gradient-to-br from-[#061B35] via-[#0A66C2] to-[#5B5CE2] px-5 pb-12 pt-24 sm:px-8 lg:px-12"
        style={{
          fontFamily:
            '"SF Pro Display", "SF Pro Text", Inter, "Helvetica Neue", Arial, sans-serif',
        }}
      >

        <div
          aria-hidden="true"
          className="absolute -right-24 -top-24 h-96 w-96 rounded-full bg-cyan-300/20 blur-3xl"
        />

        <div
          aria-hidden="true"
          className="absolute -bottom-36 -left-24 h-[30rem] w-[30rem] rounded-full bg-violet-300/20 blur-3xl"
        />


        <div className="absolute left-0 right-0 top-0 z-20 border-b border-white/10 bg-[#061B35]/20 px-5 py-4 backdrop-blur-sm sm:px-8 lg:px-12">

          <div className="mx-auto flex max-w-6xl items-center justify-end">

            <Link
              href="/login"
              className="rounded-lg bg-white px-4 py-2 text-sm font-bold text-[#0A66C2] shadow-sm transition hover:bg-blue-50 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-white/80"
            >
              Sign up / Log in
            </Link>

          </div>

        </div>


        <div className="relative z-10 mx-auto w-full max-w-6xl text-center">

          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-blue-100 sm:text-sm">
            Search smarter. Tailor faster. Apply with clarity.
          </p>


          <h1
            className="mt-4 text-5xl font-black tracking-tight text-white sm:text-6xl lg:text-7xl"
            style={{
              fontFamily:
                '"SF Pro Display", "SF Pro Text", Inter, "Helvetica Neue", Arial, sans-serif',
            }}
          >
            CareerCompass
          </h1>


          <p
            className="mx-auto mt-6 max-w-4xl text-2xl font-semibold leading-tight text-orange-300 sm:text-3xl"
            style={{
              fontFamily:
                '"Avenir Next", "Helvetica Neue", Arial, sans-serif',
              fontStyle:
                "italic",
            }}
          >
            Pass AI resume screening with confidence. 
          </p>


          <div className="mx-auto mt-8 grid max-w-5xl gap-3 sm:grid-cols-2 lg:grid-cols-4">

            {[
              "Know What to Highlight",
              "See What Is Missing",
              "Tailor Your Resume",
              "Track Your Progress",
            ].map(
              (label) => (
                <div
                  key={label}
                  aria-disabled="true"
                  className="cursor-not-allowed rounded-2xl border border-white/20 bg-white/10 px-4 py-5 text-center opacity-75 shadow-sm backdrop-blur-sm"
                >
                  <span className="text-sm font-bold text-white">
                    {label}
                  </span>
                </div>
              )
            )}

          </div>


          <div
            id="careercompass-search"
            className="mx-auto mt-9 max-w-4xl"
          >

            <p className="text-sm font-semibold uppercase tracking-[0.14em] text-blue-100">
              Find your next role
            </p>


            <div className="mt-3 grid gap-3 rounded-2xl border border-white/25 bg-white/10 p-3 shadow-2xl backdrop-blur-md md:grid-cols-[2fr_1fr_auto]">

              <input
                type="text"
                disabled
                aria-label="Role search requires sign in"
                placeholder="Role, e.g. Data Analyst Intern"
                className="min-h-12 cursor-not-allowed rounded-xl border border-white/20 bg-white/80 px-4 py-3 text-sm text-slate-500 outline-none placeholder:text-slate-400"
              />


              <input
                type="text"
                disabled
                aria-label="Location requires sign in"
                value="Singapore"
                readOnly
                className="min-h-12 cursor-not-allowed rounded-xl border border-white/20 bg-white/80 px-4 py-3 text-sm text-slate-500 outline-none"
              />


              <div className="flex gap-2 md:flex-col lg:flex-row">

                <button
                  type="button"
                  disabled
                  className="inline-flex min-h-12 flex-1 cursor-not-allowed items-center justify-center gap-2 rounded-xl bg-white/75 px-5 py-3 text-sm font-bold text-[#0A66C2] opacity-70"
                >
                  <LockIcon />
                  Search Jobs
                </button>


                <button
                  type="button"
                  disabled
                  className="inline-flex min-h-12 flex-1 cursor-not-allowed items-center justify-center gap-2 rounded-xl border border-white/30 bg-white/10 px-5 py-3 text-sm font-bold text-white/80 opacity-70"
                >
                  <LockIcon />
                  Upload Resume
                </button>

              </div>

            </div>


            <div className="mt-4 flex flex-col items-center justify-center gap-2 rounded-xl border border-white/20 bg-[#061B35]/25 px-4 py-3 text-sm text-blue-50 backdrop-blur-sm sm:flex-row">
              <LockIcon />

              <span>
                Sign up or log in to search roles, compare your resume and manage applications.
              </span>
            </div>

          </div>


          <div className="mx-auto mt-9 max-w-6xl rounded-3xl border-2 border-white/80 bg-white/95 p-5 text-slate-900 shadow-2xl backdrop-blur-md sm:p-6">

            <div className="flex flex-col items-center gap-2">

              <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-bold uppercase tracking-[0.16em] text-[#0A66C2]">
                Your Workspace
              </span>


              <p className="max-w-2xl text-sm font-medium text-slate-600">
                Create an account or sign in to unlock your personal workspace.
              </p>

            </div>


            <div
              aria-label="CareerCompass locked dashboard sections"
              className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
            >

              {[
                [
                  "Job Matches",
                  "Search and review relevant roles",
                ],
                [
                  "My Applications",
                  "Save and track applications",
                ],
                [
                  "Career Insights",
                  "See recurring skills across roles",
                ],
                [
                  "My Profile",
                  "Upload and manage your resume",
                ],
              ].map(
                ([title, description]) => (
                  <div
                    key={title}
                    aria-disabled="true"
                    className="cursor-not-allowed rounded-xl border border-slate-200 bg-slate-50 px-4 py-4 text-center opacity-70"
                  >
                    <div className="mx-auto mb-2 flex w-fit items-center gap-1.5 text-slate-400">
                      <LockIcon />
                      <span className="text-xs font-semibold uppercase tracking-wide">
                        Locked
                      </span>
                    </div>

                    <span className="block text-sm font-bold text-slate-700">
                      {title}
                    </span>

                    <span className="mt-1 block text-xs text-slate-500">
                      {description}
                    </span>
                  </div>
                )
              )}

            </div>


            <Link
              href="/login"
              className="mx-auto mt-6 inline-flex items-center justify-center rounded-xl bg-[#0A66C2] px-5 py-3 text-sm font-bold text-white shadow-sm transition hover:bg-blue-700 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500/40"
            >
              Sign up / Log in to continue
            </Link>

          </div>

        </div>

      </section>

    </main>
  );
}
