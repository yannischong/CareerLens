"use client";

import {
  useEffect,
} from "react";


type CareerCompassHelpProps = {
  open: boolean;
  onClose: () => void;
};


type HelpStepProps = {
  number: string;
  title: string;
  children: React.ReactNode;
};


function HelpStep({
  number,
  title,
  children,
}: HelpStepProps) {
  return (
    <div className="flex gap-4">

      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-[#0A66C2]">
        {
          number
        }
      </div>


      <div>

        <h3 className="font-bold text-slate-900">
          {
            title
          }
        </h3>


        <div className="mt-1 text-sm leading-6 text-slate-600">
          {
            children
          }
        </div>

      </div>

    </div>
  );
}


export function CareerCompassHelp({
  open,
  onClose,
}: CareerCompassHelpProps) {
  useEffect(
    () => {
      if (!open) {
        return;
      }


      function handleKeyDown(
        event: KeyboardEvent
      ) {
        if (
          event.key
          === "Escape"
        ) {
          onClose();
        }
      }


      window.addEventListener(
        "keydown",
        handleKeyDown
      );


      const previousOverflow =
        document.body.style
          .overflow;


      document.body.style
        .overflow = "hidden";


      return () => {
        window.removeEventListener(
          "keydown",
          handleKeyDown
        );


        document.body.style
          .overflow =
            previousOverflow;
      };
    },
    [
      open,
      onClose,
    ]
  );


  if (!open) {
    return null;
  }


  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="careercompass-help-title"
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-slate-950/60 px-4 py-8 backdrop-blur-sm sm:py-12"
      onMouseDown={
        (
          event
        ) => {
          if (
            event.target
            === event.currentTarget
          ) {
            onClose();
          }
        }
      }
    >

      <div className="w-full max-w-3xl rounded-3xl border border-slate-200 bg-white text-left text-slate-900 shadow-2xl">

        <div className="sticky top-0 z-10 flex items-start justify-between gap-4 rounded-t-3xl border-b border-slate-200 bg-white/95 px-6 py-5 backdrop-blur sm:px-8">

          <div>

            <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#0A66C2]">
              CareerCompass Guide
            </p>


            <h2
              id="careercompass-help-title"
              className="mt-1 text-2xl font-black tracking-tight text-slate-900"
            >
              How to use CareerCompass
            </h2>


            <p className="mt-1 max-w-2xl text-sm text-slate-600">
              Use CareerCompass to analyse a specific job first, compare its requirements with your resume, discover more opportunities when needed, and keep your applications organised.
            </p>

          </div>


          <button
            type="button"
            onClick={
              onClose
            }
            aria-label="Close CareerCompass guide"
            className="rounded-full border border-slate-200 px-3 py-1.5 text-sm font-bold text-slate-500 transition hover:bg-slate-100 hover:text-slate-900"
          >
            ×
          </button>

        </div>


        <div className="space-y-8 px-6 py-6 sm:px-8 sm:py-8">

          <section>

            <h3 className="text-lg font-black text-slate-900">
              Recommended workflow
            </h3>


            <div className="mt-5 space-y-6">

              <HelpStep
                number="1"
                title="Upload your resume"
              >
                Upload your resume in <strong>My Profile</strong>, or use <strong>Upload Resume</strong> beside the main job analyser. CareerCompass extracts the profile evidence used for job comparisons.
              </HelpStep>


              <HelpStep
                number="2"
                title="Analyse the job you want"
              >
                Paste the public URL of a specific role into the main analyser and select <strong>Read Job Listing</strong>. Manual job links do not use one of your two provider searches.
              </HelpStep>


              <HelpStep
                number="3"
                title="Review the extracted role"
              >
                CareerCompass reads the listing and extracts its requirements. If the page blocks automated reading, use the option to paste the job description manually instead.
              </HelpStep>


              <HelpStep
                number="4"
                title="Compare it with your resume"
              >
                Review what is <strong>Supported by your resume</strong>, <strong>Not shown on your resume</strong>, or <strong>Needs review</strong>. “Not shown” means CareerCompass did not find supporting evidence; it does not prove you do not have that skill.
              </HelpStep>


              <HelpStep
                number="5"
                title="Search for more opportunities"
              >
                If you want alternatives, use <strong>Search Jobs</strong> beneath the main analyser to search your desired role. Provider searches are limited and their results are saved automatically.
              </HelpStep>


              <HelpStep
                number="6"
                title="Save and track your progress"
              >
                Save roles to <strong>My Applications</strong>, move them through stages such as To Apply, Applied, Online Assessment, Interview and Offer, and use <strong>Career Insights</strong> to review recurring requirement gaps.
              </HelpStep>

            </div>

          </section>


          <section className="rounded-2xl border border-slate-200 bg-slate-50 p-5">

            <h3 className="text-lg font-black text-slate-900">
              What each workspace does
            </h3>


            <div className="mt-4 grid gap-3 sm:grid-cols-2">

              <div className="rounded-xl border border-slate-200 bg-white p-4">

                <p className="font-bold text-slate-900">
                  Job Matches
                </p>


                <p className="mt-1 text-sm leading-6 text-slate-600">
                  Review roles returned by provider search, inspect extracted requirements, and save interesting opportunities. Use the main analyser when you already have a specific job listing.
                </p>

              </div>


              <div className="rounded-xl border border-slate-200 bg-white p-4">

                <p className="font-bold text-slate-900">
                  My Applications
                </p>


                <p className="mt-1 text-sm leading-6 text-slate-600">
                  Track saved roles, update application stages, log activity, reopen postings and view resume comparisons.
                </p>

              </div>


              <div className="rounded-xl border border-slate-200 bg-white p-4">

                <p className="font-bold text-slate-900">
                  Career Insights
                </p>


                <p className="mt-1 text-sm leading-6 text-slate-600">
                  See recurring requirements that are supported, missing from your current profile evidence, or still need review.
                </p>

              </div>


              <div className="rounded-xl border border-slate-200 bg-white p-4">

                <p className="font-bold text-slate-900">
                  My Profile
                </p>


                <p className="mt-1 text-sm leading-6 text-slate-600">
                  Upload and review resumes and manage the profile information CareerCompass uses for role comparisons.
                </p>

              </div>

            </div>

          </section>


          <section className="rounded-2xl border border-blue-200 bg-blue-50 p-5">

            <h3 className="font-black text-blue-950">
              Understanding CareerCompass results
            </h3>


            <p className="mt-2 text-sm leading-6 text-blue-900">
              Search Relevance tells you how closely a role matches your search. Resume Comparison tells you whether CareerCompass found supporting evidence in your profile for the role’s requirements. Eligibility checks are separate again. These signals answer different questions and should not be treated as a hiring probability.
            </p>

          </section>

        </div>

      </div>

    </div>
  );
}
