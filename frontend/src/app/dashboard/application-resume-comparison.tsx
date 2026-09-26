"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  createClient,
} from "@/lib/supabase/client";

import {
  LoadingSpinner,
} from "./loading-spinner";


const DEFAULT_API_URL =
  "https://careercompass-api-2v4r.onrender.com";


function getApiBaseUrl() {
  const configured =
    process.env
      .NEXT_PUBLIC_API_URL
      ?.trim();

  return (
    configured
      || DEFAULT_API_URL
  ).replace(
    /\/+$/,
    ""
  );
}


type ManualJobConcept = {
  name: string;
  type: string;
  confidence:
    number | null;
};


type ManualJobRequirement = {
  requirement_type: string;
  requirement_level:
    string | null;
  text: string;
  normalized_text: string;
  concepts?: ManualJobConcept[];
};


type ManualJobPreview = {
  url: string;
  title: string;
  company: string | null;
  location: string | null;
  employment_type:
    string | null;
  date_posted:
    string | null;
  description: string;
  description_characters:
    number;
  extraction_method:
    string;
  needs_description:
    boolean;
  requirement_count:
    number;
  requirements:
    ManualJobRequirement[];
};


type FitConcept = {
  concept_id: number;
  name: string;
  type: string;
  claim_status: string;
  evidence_status: string;
  fit_status: string;
  model_evidence?:
    string | null;
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
  concepts: FitConcept[];
};


type FitSummary = {
  total_requirement_groups:
    number;
  evidenced_requirement_groups:
    number;
  claimed_only_requirement_groups:
    number;
  candidate_requirement_groups:
    number;
  gap_requirement_groups:
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
    Array<{
      requirement_mention_id:
        number;
      text: string;
    }>;
};


type UnavailableProfileFit = {
  status:
    | "no_resume"
    | "insufficient_job_data";
  model_version: string;
  reason: string;
};


type ManualJobAnalysis = {
  profile_available:
    boolean;
  profile_fit:
    | AssessedProfileFit
    | UnavailableProfileFit;
  resume_id?:
    number | null;
  resume_filename?:
    string | null;
  cached?: boolean;
};


type SnapshotResponse = {
  job_id: number;
  listing_snapshot:
    ManualJobPreview | null;
  resume_fit_snapshot:
    ManualJobAnalysis | null;
  resume_id:
    number | null;
  resume_filename:
    string | null;
  latest_resume_id:
    number | null;
  latest_resume_filename:
    string | null;
  resume_fit_current:
    boolean;
  analysis_version:
    string;
};


type DisplaySkill = {
  name: string;
  type: string;
  level: string;
};


type DisplayLogistical = {
  text: string;
  type: string;
};


const LOGISTICAL_REQUIREMENT_TYPES =
  new Set([
    "education",
    "experience",
    "work_authorization",
    "availability",
    "certification",
    "professional_registration",
    "licence",
    "language",
    "security_clearance",
    "physical_requirement",
  ]);


const LOGISTICAL_TEXT_PATTERN =
  /\b(penultimate|final[- ]year|year\s*[1-6]|first[- ]year|second[- ]year|third[- ]year|fourth[- ]year|currently pursuing|pursuing a|expected graduation|graduat(?:e|ing|ion)|bachelor|master|degree|diploma|commit(?:ment)?|minimum\s+\d+\s+(?:months?|weeks?)|internship period|available for|full[- ]time|part[- ]time|start date|work authori[sz]ation|eligible to work|citizenship|visa sponsorship)\b/i;


function levelRank(
  level: string
) {
  if (level === "required") {
    return 3;
  }

  if (level === "preferred") {
    return 2;
  }

  return 1;
}


function collectSkills(
  requirements:
    ManualJobRequirement[]
) {
  const byKey = new Map<
    string,
    DisplaySkill
  >();

  requirements.forEach(
    (requirement) => {
      (
        requirement.concepts
        ?? []
      ).forEach(
        (concept) => {
          if (
            concept.type
            !== "hard_skill"
            && concept.type
            !== "soft_skill"
          ) {
            return;
          }

          const level =
            requirement.requirement_level
            ?? "unknown";

          const key =
            `${concept.type}:${concept.name.toLowerCase()}`;

          const current =
            byKey.get(key);

          if (
            !current
            || levelRank(level)
              > levelRank(
                  current.level
                )
          ) {
            byKey.set(
              key,
              {
                name: concept.name,
                type: concept.type,
                level,
              }
            );
          }
        }
      );
    }
  );

  return Array.from(
    byKey.values()
  );
}


function collectLogistics(
  requirements:
    ManualJobRequirement[]
) {
  const seen = new Set<
    string
  >();

  const results:
    DisplayLogistical[] = [];

  requirements.forEach(
    (requirement) => {
      const text =
        requirement.text.trim();

      if (!text) {
        return;
      }

      if (
        !LOGISTICAL_REQUIREMENT_TYPES.has(
          requirement.requirement_type
        )
        && !LOGISTICAL_TEXT_PATTERN.test(
          text
        )
      ) {
        return;
      }

      const key =
        text
          .toLowerCase()
          .replace(/\s+/g, " ");

      if (seen.has(key)) {
        return;
      }

      seen.add(key);

      results.push(
        {
          text,
          type:
            requirement.requirement_type,
        }
      );
    }
  );

  return results;
}


function logisticalLabel(
  type: string
) {
  if (type === "education") {
    return "Education / study stage";
  }

  if (type === "availability") {
    return "Commitment / availability";
  }

  if (type === "work_authorization") {
    return "Work eligibility";
  }

  return type
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase()
    );
}


function fitLabel(
  status: string
) {
  if (status === "evidenced") {
    return "Supported by your resume";
  }

  if (status === "gap") {
    return "Not shown on your resume";
  }

  if (
    status === "claimed_only"
    || status === "candidate"
  ) {
    return "Partially supported";
  }

  return "Needs review";
}


function fitClassName(
  status: string
) {
  if (status === "evidenced") {
    return (
      "border-emerald-200 "
      + "bg-emerald-50 "
      + "text-emerald-800"
    );
  }

  if (status === "gap") {
    return (
      "border-rose-200 "
      + "bg-rose-50 "
      + "text-rose-800"
    );
  }

  return (
    "border-amber-200 "
    + "bg-amber-50 "
    + "text-amber-800"
  );
}


type Props = {
  opportunityId: number;
  jobId: number;
};


export function ApplicationResumeComparison({
  opportunityId,
  jobId,
}: Props) {
  const [
    snapshot,
    setSnapshot,
  ] = useState<
    SnapshotResponse | null
  >(null);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    comparing,
    setComparing,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);

  const [
    detailsVisible,
    setDetailsVisible,
  ] = useState(true);


  const getAccessToken =
    useCallback(
      async () => {
        const supabase =
          createClient();

        const {
          data: {
            session,
          },
        } =
          await supabase.auth
            .getSession();

        return (
          session
            ?.access_token
          ?? null
        );
      },
      []
    );


  const loadSnapshot =
    useCallback(
      async () => {
        const token =
          await getAccessToken();

        if (!token) {
          setError(
            "Your session has expired."
          );
          setLoading(false);
          return;
        }

        const response =
          await fetch(
            (
              getApiBaseUrl()
              + "/api/manual-jobs/"
              + jobId
              + "/snapshot"
            ),
            {
              headers: {
                Authorization:
                  `Bearer ${token}`,
              },
              cache: "no-store",
            }
          );

        if (!response.ok) {
          if (
            response.status
            === 404
          ) {
            setSnapshot(null);
            setLoading(false);
            return;
          }

          throw new Error(
            "CareerCompass could not load the saved analysis."
          );
        }

        setSnapshot(
          await response.json()
        );
        setLoading(false);
      },
      [
        getAccessToken,
        jobId,
      ]
    );


  useEffect(
    () => {
      loadSnapshot()
        .catch(
          (err) => {
            setError(
              err instanceof Error
                ? err.message
                : (
                  "CareerCompass could not load the saved analysis."
                )
            );
            setLoading(false);
          }
        );
    },
    [loadSnapshot]
  );


  async function compareResume() {
    setComparing(true);
    setError(null);

    try {
      const token =
        await getAccessToken();

      if (!token) {
        throw new Error(
          "Your session has expired."
        );
      }

      const response =
        await fetch(
          (
            getApiBaseUrl()
            + "/api/manual-jobs/"
            + jobId
            + "/analyze"
          ),
          {
            method: "POST",
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
              "CareerCompass could not compare this role with your resume."
            )
        );
      }

      await loadSnapshot();
      return true;

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : (
            "CareerCompass could not compare this role with your resume."
          )
      );
      return false;

    } finally {
      setComparing(false);
    }
  }


  async function showComparisonDetails() {
    if (!snapshot?.latest_resume_id) {
      setDetailsVisible(true);
      return;
    }

    if (
      snapshot.resume_fit_snapshot
      && snapshot.resume_fit_current
    ) {
      setDetailsVisible(true);
      return;
    }

    const compared =
      await compareResume();

    if (compared) {
      setDetailsVisible(true);
    }
  }


  const listing =
    snapshot?.listing_snapshot
    ?? null;

  const skills =
    useMemo(
      () =>
        collectSkills(
          listing?.requirements
          ?? []
        ),
      [listing]
    );

  const hardSkills =
    skills.filter(
      (skill) =>
        skill.type
        === "hard_skill"
    );

  const softSkills =
    skills.filter(
      (skill) =>
        skill.type
        === "soft_skill"
    );

  const logistics =
    useMemo(
      () =>
        collectLogistics(
          listing?.requirements
          ?? []
        ),
      [listing]
    );

  const fit =
    snapshot
      ?.resume_fit_snapshot
      ?.profile_fit
    ?? null;

  const assessed =
    fit?.status
    === "assessed"
      ? fit
      : null;


  if (loading) {
    return (
      <div
        data-opportunity-id={
          opportunityId
        }
        className="mt-4 flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500"
      >
        <LoadingSpinner
          label="Loading saved analysis"
        />
        Loading saved analysis...
      </div>
    );
  }


  if (!listing) {
    return (
      <div
        data-opportunity-id={
          opportunityId
        }
        className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900"
      >
        This older saved job does not have a CareerCompass analysis snapshot. Open the posting and use Analyse Job to add the full listing analysis.
      </div>
    );
  }


  if (!detailsVisible) {
    return (
      <div
        data-opportunity-id={opportunityId}
        className="mt-4 rounded-xl border border-slate-200 bg-slate-50/70 p-4"
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-bold text-slate-900">
              Job analysis hidden
            </p>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              The saved analysis and resume comparison are still stored.
            </p>
          </div>

          <button
            type="button"
            onClick={showComparisonDetails}
            disabled={comparing}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#0A66C2] px-4 py-2.5 text-sm font-bold text-white hover:bg-[#004182] disabled:opacity-50"
          >
            {comparing && (
              <LoadingSpinner label="Comparing with your resume" />
            )}
            {comparing ? "Comparing..." : "Compare Resume"}
          </button>
        </div>

        {error && (
          <div className="mt-3 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
            {error}
          </div>
        )}
      </div>
    );
  }


  return (
    <div
      data-opportunity-id={
        opportunityId
      }
      className="mt-4 space-y-4 rounded-xl border border-slate-200 bg-slate-50/70 p-4"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-bold text-slate-900">
            Saved job analysis
          </p>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            This is the same stored analysis produced by Analyse Job. Viewing it again does not use model tokens.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-slate-600">
            {listing.requirement_count} requirements
          </span>
          <button
            type="button"
            onClick={() => setDetailsVisible(false)}
            className="rounded-lg border border-[#0A66C2] bg-[#0A66C2] px-3 py-1.5 text-xs font-bold text-white transition hover:bg-[#004182]"
          >
            Hide Details
          </button>
        </div>
      </div>


      <div>
        <p className="text-sm font-semibold text-slate-900">
          Extracted requirements
        </p>

        <div className="mt-3 grid gap-3 md:grid-cols-3">
          <div className="rounded-lg border border-blue-100 bg-white p-3">
            <p className="text-xs font-bold uppercase tracking-wide text-[#0A66C2]">
              Hard skills
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {hardSkills.length > 0 ? hardSkills.map((skill) => (
                <span
                  key={`hard-${skill.name}`}
                  className="rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-800"
                >
                  {skill.name}
                </span>
              )) : (
                <span className="text-xs text-slate-500">
                  None confidently identified.
                </span>
              )}
            </div>
          </div>

          <div className="rounded-lg border border-violet-100 bg-white p-3">
            <p className="text-xs font-bold uppercase tracking-wide text-violet-700">
              Soft skills
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {softSkills.length > 0 ? softSkills.map((skill) => (
                <span
                  key={`soft-${skill.name}`}
                  className="rounded-full border border-violet-200 bg-violet-50 px-2.5 py-1 text-xs font-semibold text-violet-800"
                >
                  {skill.name}
                </span>
              )) : (
                <span className="text-xs text-slate-500">
                  None confidently identified.
                </span>
              )}
            </div>
          </div>

          <div className="rounded-lg border border-emerald-100 bg-white p-3">
            <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">
              Eligibility
            </p>
            {logistics.length > 0 ? (
              <div className="mt-2 space-y-2">
                {logistics.map((item) => (
                  <div
                    key={`${item.type}-${item.text}`}
                    className="rounded border border-emerald-100 bg-emerald-50/60 p-2"
                  >
                    <p className="text-[11px] font-bold uppercase tracking-wide text-emerald-700">
                      {logisticalLabel(item.type)}
                    </p>
                    <p className="mt-1 text-xs leading-5 text-slate-700">
                      {item.text}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-2 text-xs text-slate-500">
                None clearly identified.
              </p>
            )}
          </div>
        </div>
      </div>


      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          {error}
        </div>
      )}


      {!snapshot?.latest_resume_id ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
          Upload a resume to compare it with this role.
        </div>
      ) : !snapshot.resume_fit_snapshot ? (
        <button
          type="button"
          onClick={
            compareResume
          }
          disabled={
            comparing
          }
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#0A66C2] px-4 py-2.5 text-sm font-bold text-white hover:bg-[#004182] disabled:opacity-50"
        >
          {comparing && (
            <LoadingSpinner
              label="Comparing with your resume"
            />
          )}
          {comparing
            ? "Comparing..."
            : "Compare With My Resume"}
        </button>
      ) : (
        <>
          {!snapshot.resume_fit_current && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
              This saved comparison used {snapshot.resume_filename ?? "an earlier resume"}. Your current resume is {snapshot.latest_resume_filename ?? "different"}.
              <button
                type="button"
                onClick={compareResume}
                disabled={comparing}
                className="ml-2 font-semibold underline"
              >
                {comparing
                  ? "Comparing..."
                  : "Compare with current resume"}
              </button>
            </div>
          )}

          {fit && fit.status !== "assessed" && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
              {fit.reason}
            </div>
          )}

          {assessed && (
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-bold text-slate-900">
                    Resume comparison
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    Saved from {snapshot.resume_filename ?? "your resume"}.
                  </p>
                </div>

                {snapshot.resume_fit_current && (
                  <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-800">
                    Saved result · no new tokens used
                  </span>
                )}
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3">
                  <p className="text-2xl font-bold text-emerald-800">
                    {assessed.summary.evidenced_requirement_groups}
                  </p>
                  <p className="mt-1 text-xs font-semibold text-emerald-700">
                    Supported
                  </p>
                </div>

                <div className="rounded-lg border border-rose-200 bg-rose-50 p-3">
                  <p className="text-2xl font-bold text-rose-800">
                    {assessed.summary.gap_requirement_groups}
                  </p>
                  <p className="mt-1 text-xs font-semibold text-rose-700">
                    Not shown
                  </p>
                </div>

                <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
                  <p className="text-2xl font-bold text-amber-800">
                    {
                      assessed.summary.candidate_requirement_groups
                      + assessed.summary.claimed_only_requirement_groups
                      + assessed.summary.unresolved_requirements
                    }
                  </p>
                  <p className="mt-1 text-xs font-semibold text-amber-700">
                    Partial / review
                  </p>
                </div>
              </div>

              <div className="mt-4 space-y-3">
                {assessed.groups.map((group) => (
                  <div
                    key={group.requirement_mention_id}
                    className="rounded-lg border border-slate-200 p-3"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <p className="max-w-2xl text-sm font-medium leading-6 text-slate-800">
                        {group.text}
                      </p>
                      <span
                        className={
                          "rounded-full border px-2.5 py-1 text-xs font-semibold "
                          + fitClassName(group.status)
                        }
                      >
                        {fitLabel(group.status)}
                      </span>
                    </div>

                    {group.concepts.length > 0 && (
                      <div className="mt-3 space-y-2">
                        {group.concepts.map((concept) => (
                          <div
                            key={`${group.requirement_mention_id}-${concept.concept_id}`}
                            className="rounded-lg bg-slate-50 px-3 py-2"
                          >
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <span className="text-xs font-semibold text-slate-700">
                                {concept.name}
                              </span>
                              <span
                                className={
                                  "rounded-full border px-2 py-0.5 text-[11px] font-semibold "
                                  + fitClassName(concept.fit_status)
                                }
                              >
                                {fitLabel(concept.fit_status)}
                              </span>
                            </div>

                            {concept.model_evidence && (
                              <p className="mt-2 text-xs leading-5 text-slate-600">
                                <span className="font-semibold text-slate-700">
                                  Resume evidence:
                                </span>{" "}
                                “{concept.model_evidence}”
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      <div className="border-t border-slate-200 pt-4">
        <button
          type="button"
          onClick={() => setDetailsVisible(false)}
          className="w-full rounded-lg border border-[#0A66C2] bg-[#0A66C2] px-4 py-2.5 text-sm font-bold text-white transition hover:bg-[#004182]"
        >
          Hide Details
        </button>
      </div>
    </div>
  );
}
