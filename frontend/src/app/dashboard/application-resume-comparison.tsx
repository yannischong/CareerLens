"use client";

import {
  useState,
} from "react";

import {
  createClient,
} from "@/lib/supabase/client";


type FitConcept = {
  concept_id: number;
  name: string;
  type: string;
  claim_status: string;
  evidence_status: string;
  fit_status: string;
};


type FitGroup = {
  requirement_mention_id:
    number;
  type: string;
  level: string;
  text: string;
  operator: string;
  is_open: boolean;
  status: string;
  explanation: string;
  matched_concept_id:
    number | null;
  concepts:
    FitConcept[];
};


type UnresolvedRequirement = {
  requirement_mention_id:
    number;
  type: string;
  level: string;
  text: string;
  status: string;
  explanation: string;
};


type FitSummary = {
  total_requirement_groups:
    number;
  required_requirement_groups:
    number;
  preferred_requirement_groups:
    number;
  evidenced_requirement_groups:
    number;
  claimed_only_requirement_groups:
    number;
  candidate_requirement_groups:
    number;
  gap_requirement_groups:
    number;
  required_candidate_groups:
    number;
  required_gap_groups:
    number;
  unresolved_requirements:
    number;
};


type AssessedProfileFit = {
  status: "assessed";
  model_version: string;
  summary: FitSummary;
  groups: FitGroup[];
  unresolved_requirements:
    UnresolvedRequirement[];
};


type UnavailableProfileFit = {
  status:
    | "no_resume"
    | "insufficient_job_data";
  model_version: string;
  reason: string;
};


type JobAnalysis = {
  profile_available:
    boolean;
  profile_fit:
    | AssessedProfileFit
    | UnavailableProfileFit;
};


type ApplicationResumeComparisonProps = {
  opportunityId: number;
};


function fitLabel(
  status: string
) {
  if (
    status
    === "evidenced"
  ) {
    return (
      "Supported by your resume"
    );
  }


  if (
    status
    === "gap"
  ) {
    return (
      "Not shown on your resume"
    );
  }


  if (
    status
    === "claimed_only"
  ) {
    return (
      "Mentioned, but evidence is limited"
    );
  }


  return "Needs review";
}


function fitClassName(
  status: string
) {
  if (
    status
    === "evidenced"
  ) {
    return (
      "border-emerald-200 bg-emerald-50 text-emerald-800"
    );
  }


  if (
    status
    === "gap"
  ) {
    return (
      "border-rose-200 bg-rose-50 text-rose-800"
    );
  }


  return (
    "border-amber-200 bg-amber-50 text-amber-800"
  );
}


export function ApplicationResumeComparison({
  opportunityId,
}: ApplicationResumeComparisonProps) {
  const [
    open,
    setOpen,
  ] = useState(
    false
  );


  const [
    loading,
    setLoading,
  ] = useState(
    false
  );


  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);


  const [
    analysis,
    setAnalysis,
  ] = useState<
    JobAnalysis | null
  >(null);


  async function loadComparison() {
    setOpen(
      true
    );

    setLoading(
      true
    );

    setError(
      null
    );


    const supabase =
      createClient();


    const {
      data: {
        session,
      },
    } =
      await supabase.auth
        .getSession();


    const token =
      session
        ?.access_token;


    if (!token) {
      setError(
        "Your session has expired."
      );

      setLoading(
        false
      );

      return;
    }


    const apiUrl =
      process.env
        .NEXT_PUBLIC_API_URL;


    try {
      const response =
        await fetch(
          (
            `${apiUrl}`
            + `/api/opportunities/${opportunityId}/resume-comparison`
          ),
          {
            method:
              "POST",

            headers: {
              Authorization:
                `Bearer ${token}`,
            },
          }
        );


      const data =
        await response.json();


      if (!response.ok) {
        throw new Error(
          typeof data.detail
          === "string"
            ? data.detail
            : (
              "CareerCompass could not load this resume comparison."
            )
        );
      }


      setAnalysis(
        data as JobAnalysis
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : (
            "CareerCompass could not load this resume comparison."
          )
      );

    } finally {
      setLoading(
        false
      );
    }
  }


  function handleToggle() {
    if (open) {
      setOpen(
        false
      );

      return;
    }


    void loadComparison();
  }


  let assessedFit:
    AssessedProfileFit
    | null = null;


  let unavailableFit:
    UnavailableProfileFit
    | null = null;


  if (
    analysis
    && analysis
      .profile_fit
      .status
      === "assessed"
  ) {
    assessedFit =
      analysis.profile_fit;
  }


  if (
    analysis
    && analysis
      .profile_fit
      .status
      !== "assessed"
  ) {
    unavailableFit =
      analysis.profile_fit;
  }


  return (
    <div className="mt-4">

      <button
        type="button"
        onClick={
          handleToggle
        }
        disabled={
          loading
        }
        className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-semibold text-[#0A66C2] hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {
          loading
            ? "Refreshing comparison..."
            : open
              ? "Close Resume Comparison"
              : "View Resume Comparison"
        }
      </button>


      {
        open
        && (
          <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50/70 p-4">

            {
              loading
              && (
                <p className="text-sm text-slate-600">
                  Comparing this role with your latest CareerCompass profile...
                </p>
              )
            }


            {
              error
              && (
                <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
                  {
                    error
                  }
                </div>
              )
            }


            {
              !loading
              && unavailableFit
              && (
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">

                  <p className="font-semibold text-amber-900">
                    Resume comparison unavailable
                  </p>


                  <p className="mt-1 text-sm text-amber-800">
                    {
                      unavailableFit.reason
                    }
                  </p>

                </div>
              )
            }


            {
              !loading
              && assessedFit
              && (
                <div>

                  <div className="flex flex-wrap items-start justify-between gap-3">

                    <div>

                      <p className="text-xs font-bold uppercase tracking-wide text-[#0A66C2]">
                        Your profile vs this role
                      </p>


                      <h4 className="mt-1 text-lg font-bold text-slate-900">
                        Resume comparison
                      </h4>

                    </div>


                    <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600">
                      {
                        assessedFit
                          .summary
                          .total_requirement_groups
                      }{" "}
                      assessable requirements
                    </span>

                  </div>


                  <div className="mt-4 grid gap-3 sm:grid-cols-3">

                    <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3">

                      <p className="text-2xl font-bold text-emerald-800">
                        {
                          assessedFit
                            .summary
                            .evidenced_requirement_groups
                        }
                      </p>


                      <p className="mt-1 text-xs font-semibold text-emerald-700">
                        Supported by your resume
                      </p>

                    </div>


                    <div className="rounded-lg border border-rose-200 bg-rose-50 p-3">

                      <p className="text-2xl font-bold text-rose-800">
                        {
                          assessedFit
                            .summary
                            .gap_requirement_groups
                        }
                      </p>


                      <p className="mt-1 text-xs font-semibold text-rose-700">
                        Not shown on your resume
                      </p>

                    </div>


                    <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">

                      <p className="text-2xl font-bold text-amber-800">
                        {
                          assessedFit
                            .summary
                            .candidate_requirement_groups
                          +
                          assessedFit
                            .summary
                            .claimed_only_requirement_groups
                          +
                          assessedFit
                            .summary
                            .unresolved_requirements
                        }
                      </p>


                      <p className="mt-1 text-xs font-semibold text-amber-700">
                        Needs review
                      </p>

                    </div>

                  </div>


                  <div className="mt-5 space-y-3">

                    {
                      assessedFit
                        .groups
                        .map(
                          (
                            group
                          ) => (
                            <div
                              key={
                                group
                                  .requirement_mention_id
                              }
                              className="rounded-lg border border-slate-200 bg-white p-3"
                            >

                              <div className="flex flex-wrap items-start justify-between gap-2">

                                <p className="max-w-2xl text-sm font-medium leading-6 text-slate-800">
                                  {
                                    group.text
                                  }
                                </p>


                                <span
                                  className={
                                    "rounded-full border px-2.5 py-1 text-xs font-semibold "
                                    + fitClassName(
                                        group.status
                                      )
                                  }
                                >
                                  {
                                    fitLabel(
                                      group.status
                                    )
                                  }
                                </span>

                              </div>


                              {
                                group
                                  .concepts
                                  .length
                                > 0
                                && (
                                  <p className="mt-2 text-xs text-slate-500">
                                    {
                                      group
                                        .concepts
                                        .map(
                                          (
                                            concept
                                          ) =>
                                            concept.name
                                        )
                                        .join(
                                          " · "
                                        )
                                    }
                                  </p>
                                )
                              }

                            </div>
                          )
                        )
                    }


                    {
                      assessedFit
                        .unresolved_requirements
                        .map(
                          (
                            requirement
                          ) => (
                            <div
                              key={
                                requirement
                                  .requirement_mention_id
                              }
                              className="rounded-lg border border-amber-200 bg-amber-50 p-3"
                            >

                              <div className="flex flex-wrap items-start justify-between gap-2">

                                <p className="max-w-2xl text-sm font-medium leading-6 text-slate-800">
                                  {
                                    requirement.text
                                  }
                                </p>


                                <span className="rounded-full border border-amber-200 bg-white px-2.5 py-1 text-xs font-semibold text-amber-800">
                                  Needs review
                                </span>

                              </div>

                            </div>
                          )
                        )
                    }

                  </div>


                  <p className="mt-4 text-xs leading-5 text-slate-500">
                    This comparison is refreshed whenever you open it. “Not shown” means CareerCompass did not find supporting evidence in your current profile; it does not prove that you do not have the skill.
                  </p>

                </div>
              )
            }

          </div>
        )
      }

    </div>
  );
}
