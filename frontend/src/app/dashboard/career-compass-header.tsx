"use client";

import {
  useState,
} from "react";

import type {
  FormEvent,
} from "react";

import {
  useRouter,
} from "next/navigation";

import {
  createClient,
} from "@/lib/supabase/client";

import {
  SearchGuidance,
} from "./search-guidance";

import {
  ManualJobImport,
} from "./manual-job-import";

import {
  CareerCompassHelp,
} from "./career-compass-help";

import {
  LoadingSpinner,
} from "./loading-spinner";


export type DashboardView =
  | "jobs"
  | "applications"
  | "insights"
  | "profile";


type CareerCompassHeaderProps = {
  activeView: DashboardView;
  onViewChange: (
    view: DashboardView
  ) => void;
  jobCount: number;
  applicationCount: number;
  resumeCount: number;
  query: string;
  location: string;
  searching: boolean;
  remainingSearches: number | null;
  searchLimit: number;
  userEmail: string;
  onQueryChange: (
    value: string
  ) => void;
  onLocationChange: (
    value: string
  ) => void;
  onSearch: (
    event:
      FormEvent<HTMLFormElement>
  ) => void;
  onOpportunitySaved:
    () => Promise<void>;
};


export function CareerCompassHeader({
  activeView,
  onViewChange,
  jobCount,
  applicationCount,
  resumeCount,
  query,
  location,
  searching,
  remainingSearches,
  searchLimit,
  userEmail,
  onQueryChange,
  onLocationChange,
  onSearch,
  onOpportunitySaved,
}: CareerCompassHeaderProps) {
  const router =
    useRouter();


  const [
    helpOpen,
    setHelpOpen,
  ] = useState(
    false
  );


  const [
    signingOut,
    setSigningOut,
  ] = useState(
    false
  );


  function navButtonClass(
    view: DashboardView
  ) {
    return (
      "rounded-xl border px-4 py-3 "
      + "text-center transition "
      + (
        activeView === view
          ? (
            "border-blue-200 bg-blue-50 "
            + "text-[#0A66C2] shadow-md"
          )
          : (
            "border-slate-200 bg-white "
            + "text-slate-700 hover:border-blue-300 "
            + "hover:bg-blue-50"
          )
      )
    );
  }


  function subtextClass(
    view: DashboardView
  ) {
    return (
      "mt-1 block text-xs "
      + (
        activeView === view
          ? "text-blue-700"
          : "text-slate-500"
      )
    );
  }


  function scrollToSearch() {
    document
      .getElementById(
        "careercompass-search"
      )
      ?.scrollIntoView(
        {
          behavior:
            "smooth",
          block:
            "center",
        }
      );


    window.setTimeout(
      () => {
        document
          .getElementById(
            "careercompass-role-search"
          )
          ?.focus();
      },
      450
    );
  }


  function openResumeUpload() {
    onViewChange(
      "profile"
    );


    window.setTimeout(
      () => {
        document
          .getElementById(
            "careercompass-resume-upload"
          )
          ?.scrollIntoView(
            {
              behavior:
                "smooth",
              block:
                "start",
            }
          );
      },
      80
    );
  }


  function openView(
    view:
      DashboardView
  ) {
    onViewChange(
      view
    );


    window.setTimeout(
      () => {
        document
          .getElementById(
            "careercompass-content"
          )
          ?.scrollIntoView(
            {
              behavior:
                "smooth",
              block:
                "start",
            }
          );
      },
      50
    );
  }


  async function handleSignOut() {
    setSigningOut(
      true
    );


    const supabase =
      createClient();


    try {
      await supabase.auth
        .signOut();


      router.push(
        "/login"
      );

      router.refresh();

    } finally {
      setSigningOut(
        false
      );
    }
  }


  return (
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

        <div className="mx-auto flex max-w-6xl items-center justify-end gap-3">

          <span className="hidden max-w-[260px] truncate text-sm font-medium text-blue-50 sm:block">
            {
              userEmail
            }
          </span>


          <button
            type="button"
            onClick={
              handleSignOut
            }
            disabled={
              signingOut
            }
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/25 bg-white/10 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {
              signingOut
                && (
                  <LoadingSpinner
                    label="Signing out"
                  />
                )
            }

            {
              signingOut
                ? "Signing out..."
                : "Sign out"
            }
          </button>

        </div>

      </div>


      <div className="relative z-10 mx-auto w-full max-w-6xl text-center">

        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">

          <div />


          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-blue-100 sm:text-sm">
            Search smarter. Tailor faster. Apply with clarity.
          </p>


          <button
            type="button"
            onClick={() =>
              setHelpOpen(
                true
              )
            }
            className="justify-self-end text-sm font-semibold text-white underline decoration-white/60 underline-offset-4 transition hover:text-blue-100 hover:decoration-white"
          >
            Need help?
          </button>

        </div>


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
          Stop guessing what companies look for in your resume.
        </p>


        <div className="mx-auto mt-8 grid max-w-5xl gap-3 sm:grid-cols-2 lg:grid-cols-4">

          <button
            type="button"
            onClick={
              scrollToSearch
            }
            className="rounded-2xl border border-white/25 bg-white/10 px-4 py-5 text-center shadow-sm backdrop-blur-sm transition hover:-translate-y-0.5 hover:border-white/50 hover:bg-white/20"
          >
            <span className="text-sm font-bold text-white">
              Know What to Highlight
            </span>
          </button>


          <button
            type="button"
            onClick={
              scrollToSearch
            }
            className="rounded-2xl border border-white/25 bg-white/10 px-4 py-5 text-center shadow-sm backdrop-blur-sm transition hover:-translate-y-0.5 hover:border-white/50 hover:bg-white/20"
          >
            <span className="text-sm font-bold text-white">
              See What Is Missing
            </span>
          </button>


          <button
            type="button"
            onClick={() =>
              openView(
                "profile"
              )
            }
            className="rounded-2xl border border-white/25 bg-white/10 px-4 py-5 text-center shadow-sm backdrop-blur-sm transition hover:-translate-y-0.5 hover:border-white/50 hover:bg-white/20"
          >
            <span className="text-sm font-bold text-white">
              Tailor Your Resume
            </span>
          </button>


          <button
            type="button"
            onClick={() =>
              openView(
                "applications"
              )
            }
            className="rounded-2xl border border-white/25 bg-white/10 px-4 py-5 text-center shadow-sm backdrop-blur-sm transition hover:-translate-y-0.5 hover:border-white/50 hover:bg-white/20"
          >
            <span className="text-sm font-bold text-white">
              Track Your Progress
            </span>
          </button>

        </div>


        <div
          id="careercompass-search"
          className="mx-auto mt-9 max-w-4xl scroll-mt-4"
        >

          <p className="text-sm font-semibold uppercase tracking-[0.14em] text-blue-100">
            Find your next role
          </p>


          <form
            onSubmit={
              onSearch
            }
            className="mt-3 grid gap-3 rounded-2xl border border-white/25 bg-white/10 p-3 shadow-2xl backdrop-blur-md md:grid-cols-[2fr_1fr_auto]"
          >

            <input
              id="careercompass-role-search"
              value={
                query
              }
              onChange={
                (event) =>
                  onQueryChange(
                    event.target.value
                  )
              }
              placeholder="Role, e.g. Data Analyst Intern"
              required
              className="min-h-12 rounded-xl border border-white/20 bg-white px-4 py-3 text-sm text-slate-900 outline-none ring-blue-300 placeholder:text-slate-400 focus:ring-2"
            />


            <input
              value={
                location
              }
              onChange={
                (event) =>
                  onLocationChange(
                    event.target.value
                  )
              }
              placeholder="Location"
              required
              className="min-h-12 rounded-xl border border-white/20 bg-white px-4 py-3 text-sm text-slate-900 outline-none ring-blue-300 placeholder:text-slate-400 focus:ring-2"
            />


            <div className="flex gap-2 md:flex-col lg:flex-row">

              <button
                type="submit"
                disabled={
                  searching
                  || remainingSearches
                    === 0
                }
                className="inline-flex min-h-12 flex-1 items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-bold text-[#0A66C2] shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50"
              >
                {
                  searching
                    && (
                      <LoadingSpinner
                        label="Searching for jobs"
                      />
                    )
                }

                {
                  searching
                    ? "Searching..."
                    : "Search Jobs"
                }
              </button>


              <button
                type="button"
                onClick={
                  openResumeUpload
                }
                className="min-h-12 flex-1 rounded-xl border border-white/40 bg-white/15 px-5 py-3 text-sm font-bold text-white shadow-sm transition hover:bg-white/25"
              >
                Upload Resume
              </button>

            </div>

          </form>


          <SearchGuidance
            remaining={
              remainingSearches
            }
            limit={
              searchLimit
            }
          />


          <ManualJobImport
            onOpportunitySaved={
              onOpportunitySaved
            }
          />

        </div>


        <div className="mx-auto mt-9 max-w-6xl rounded-3xl border-2 border-white/80 bg-white/95 p-5 text-slate-900 shadow-2xl backdrop-blur-md sm:p-6">

          <div className="flex flex-col items-center gap-2">

            <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-bold uppercase tracking-[0.16em] text-[#0A66C2]">
              Your Workspace
            </span>


            <p className="max-w-2xl text-sm font-medium text-slate-600">
              Jump straight into your saved jobs, applications, career insights or profile.
            </p>

          </div>


          <nav
            aria-label="CareerCompass dashboard sections"
            className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
          >

            <button
              type="button"
              onClick={() =>
                openView(
                  "jobs"
                )
              }
              className={
                navButtonClass(
                  "jobs"
                )
              }
            >
              <span className="block text-sm font-bold">
                Job Matches
              </span>
              <span
                className={
                  subtextClass(
                    "jobs"
                  )
                }
              >
                {jobCount} saved results
              </span>
            </button>


            <button
              type="button"
              onClick={() =>
                openView(
                  "applications"
                )
              }
              className={
                navButtonClass(
                  "applications"
                )
              }
            >
              <span className="block text-sm font-bold">
                My Applications
              </span>
              <span
                className={
                  subtextClass(
                    "applications"
                  )
                }
              >
                {applicationCount} saved and tracked
              </span>
            </button>


            <button
              type="button"
              onClick={() =>
                openView(
                  "insights"
                )
              }
              className={
                navButtonClass(
                  "insights"
                )
              }
            >
              <span className="block text-sm font-bold">
                Career Insights
              </span>
              <span
                className={
                  subtextClass(
                    "insights"
                  )
                }
              >
                Skills across your target roles
              </span>
            </button>


            <button
              type="button"
              onClick={() =>
                openView(
                  "profile"
                )
              }
              className={
                navButtonClass(
                  "profile"
                )
              }
            >
              <span className="block text-sm font-bold">
                My Profile
              </span>
              <span
                className={
                  subtextClass(
                    "profile"
                  )
                }
              >
                {resumeCount} resume
                {resumeCount === 1 ? "" : "s"} uploaded
              </span>
            </button>

          </nav>

        </div>

      </div>


      <CareerCompassHelp
        open={
          helpOpen
        }
        onClose={() =>
          setHelpOpen(
            false
          )
        }
      />

    </section>
  );
}
