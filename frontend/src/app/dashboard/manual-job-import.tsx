"use client";

import {
  FormEvent,
  useEffect,
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


const ANALYSER_DRAFT_STORAGE_KEY =
  "careercompass:manual-job-analyser-draft:v1";


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


type ImportedJob = {
  job_id: number;
  raw_title: string;
  raw_company_name: string;
  location_raw:
    string | null;
  employment_type:
    string | null;
  job_url: string;
  source: string;
  date_posted:
    string | null;
  derived_posted_date:
    string | null;
  insufficient_description:
    boolean;
};


type ManualJobImportResult = {
  created: boolean;
  job: ImportedJob;
  requirement_count: number;
  concept_link_count: number;
  opportunity_id: number;
  opportunity_created: boolean;
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
  model_confidence?:
    number | null;
  model_match_status?:
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


type ManualJobAnalysis = {
  profile_available:
    boolean;
  job: ImportedJob;
  profile_fit:
    | AssessedProfileFit
    | UnavailableProfileFit;
};



type ManualJobImportProps = {
  onOpportunitySaved?:
    () => Promise<void>;

  onResumeUpload?:
    () => void;
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
    || status
    === "candidate"
  ) {
    return (
      "Partially supported"
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


type DisplaySkillConcept = {
  name: string;
  type: string;
  level: string;
  confidence:
    number | null;
};


function requirementLevelRank(
  level: string
) {
  if (
    level === "required"
  ) {
    return 3;
  }


  if (
    level === "preferred"
  ) {
    return 2;
  }


  return 1;
}


function collectSkillConcepts(
  requirements:
    ManualJobRequirement[]
) {
  const byKey = new Map<
    string,
    DisplaySkillConcept
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


          const key = (
            concept.type
            + ":"
            + concept.name
              .trim()
              .toLowerCase()
          );


          const existing =
            byKey.get(
              key
            );


          if (
            !existing
            || requirementLevelRank(
              level
            )
            > requirementLevelRank(
              existing.level
            )
          ) {
            byKey.set(
              key,
              {
                name: concept.name,
                type: concept.type,
                level,
                confidence:
                  concept.confidence,
              }
            );

            return;
          }


          if (
            existing
            && concept.confidence
              !== null
            && (
              existing.confidence
              === null
              || concept.confidence
                > existing.confidence
            )
          ) {
            byKey.set(
              key,
              {
                ...existing,
                confidence:
                  concept.confidence,
              }
            );
          }
        }
      );
    }
  );


  return Array.from(
    byKey.values()
  ).sort(
    (a, b) =>
      a.name.localeCompare(
        b.name
      )
  );
}


type DisplayLogisticalRequirement = {
  text: string;
  type: string;
  level: string;
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


function collectLogisticalRequirements(
  requirements:
    ManualJobRequirement[]
) {
  const byKey = new Map<
    string,
    DisplayLogisticalRequirement
  >();


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

      const level =
        requirement.requirement_level
        ?? "unknown";

      const existing =
        byKey.get(key);

      if (
        !existing
        || requirementLevelRank(level)
          > requirementLevelRank(
              existing.level
            )
      ) {
        byKey.set(
          key,
          {
            text,
            type:
              requirement.requirement_type,
            level,
          }
        );
      }
    }
  );


  return Array.from(
    byKey.values()
  );
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

  if (type === "experience") {
    return "Experience";
  }

  return type
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase()
    );
}


export function ManualJobImport({
  onOpportunitySaved,
  onResumeUpload,
}: ManualJobImportProps) {
  const [
    url,
    setUrl,
  ] = useState(
    ""
  );


  const [
    manualDescription,
    setManualDescription,
  ] = useState(
    ""
  );


  const [
    showDescriptionFallback,
    setShowDescriptionFallback,
  ] = useState(
    false
  );


  const [
    cameFromJobSearch,
    setCameFromJobSearch,
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
    importing,
    setImporting,
  ] = useState(
    false
  );


  const [
    analyzing,
    setAnalyzing,
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
    preview,
    setPreview,
  ] = useState<
    ManualJobPreview | null
  >(null);


  const [
    imported,
    setImported,
  ] = useState<
    ManualJobImportResult | null
  >(null);


  const [
    analysis,
    setAnalysis,
  ] = useState<
    ManualJobAnalysis | null
  >(null);


  const [
    draftRestored,
    setDraftRestored,
  ] = useState(
    false
  );


  useEffect(() => {
    try {
      const stored =
        window.localStorage.getItem(
          ANALYSER_DRAFT_STORAGE_KEY
        );

      if (stored) {
        const draft =
          JSON.parse(stored) as {
            url?: string;
            manualDescription?: string;
            showDescriptionFallback?: boolean;
            cameFromJobSearch?: boolean;
            preview?: ManualJobPreview | null;
            imported?: ManualJobImportResult | null;
            analysis?: ManualJobAnalysis | null;
          };

        setUrl(draft.url ?? "");
        setManualDescription(
          draft.manualDescription ?? ""
        );
        setShowDescriptionFallback(
          draft.showDescriptionFallback ?? false
        );
        setCameFromJobSearch(
          draft.cameFromJobSearch ?? false
        );
        setPreview(draft.preview ?? null);
        setImported(draft.imported ?? null);
        setAnalysis(draft.analysis ?? null);
      }
    } catch {
      window.localStorage.removeItem(
        ANALYSER_DRAFT_STORAGE_KEY
      );
    } finally {
      setDraftRestored(true);
    }
  }, []);


  useEffect(() => {
    if (!draftRestored) {
      return;
    }

    window.localStorage.setItem(
      ANALYSER_DRAFT_STORAGE_KEY,
      JSON.stringify({
        url,
        manualDescription,
        showDescriptionFallback,
        cameFromJobSearch,
        preview,
        imported,
        analysis,
      })
    );
  }, [
    draftRestored,
    url,
    manualDescription,
    showDescriptionFallback,
    cameFromJobSearch,
    preview,
    imported,
    analysis,
  ]);


  useEffect(() => {
    function handleSearchJobForAnalysis(
      event: Event
    ) {
      const customEvent =
        event as CustomEvent<{
          sourceUrl?: string | null;
        }>;

      const sourceUrl =
        customEvent.detail
          ?.sourceUrl
          ?.trim();

      if (!sourceUrl) {
        return;
      }

      setUrl(
        sourceUrl
      );

      setManualDescription(
        ""
      );

      setCameFromJobSearch(
        true
      );

      setShowDescriptionFallback(
        true
      );

      setError(
        null
      );

      setPreview(
        null
      );

      setImported(
        null
      );

      setAnalysis(
        null
      );
    }


    window.addEventListener(
      "careerlens:analyse-search-job",
      handleSearchJobForAnalysis
    );


    return () => {
      window.removeEventListener(
        "careerlens:analyse-search-job",
        handleSearchJobForAnalysis
      );
    };
  }, []);


  async function getAccessToken() {
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
  }


  async function authenticatedPost(
    path: string,
    body:
      Record<
        string,
        unknown
      >
      | null
  ) {
    const token =
      await getAccessToken();


    if (!token) {
      throw new Error(
        "Your session has expired."
      );
    }


    const apiUrl =
      getApiBaseUrl();

    const requestUrl =
      `${apiUrl}${path}`;

    console.info(
      "[CareerLens manual API]",
      requestUrl
    );


    const response =
      await fetch(
        requestUrl,
        {
          method:
            "POST",

          headers: {
            "Content-Type":
              "application/json",

            Authorization:
              `Bearer ${token}`,
          },

          body:
            body === null
              ? undefined
              : JSON.stringify(
                  body
                ),
        }
      );


    const data =
      await response.json();


    return {
      response,
      data,
    };
  }


  function resetImportedState() {
    setImported(
      null
    );

    setAnalysis(
      null
    );

  }


  function requestBody() {
    return {
      url:
        url.trim(),

      description_override:
        manualDescription
          .trim()
        || null,
    };
  }


  async function handlePreview(
    event:
      FormEvent<
        HTMLFormElement
      >
  ) {
    event.preventDefault();


    if (
      !url.trim()
    ) {
      setError(
        "Paste a job listing link first."
      );

      return;
    }


    setLoading(
      true
    );

    setError(
      null
    );

    setPreview(
      null
    );

    resetImportedState();


    try {
      const {
        response,
        data,
      } =
        await authenticatedPost(
          "/api/manual-jobs/preview",
          requestBody()
        );


      if (
        !response.ok
      ) {
        const detail =
          data.detail;


        if (
          detail
          && typeof detail
          === "object"
          && detail
            .needs_description
        ) {
          setShowDescriptionFallback(
            true
          );

          throw new Error(
            typeof detail.message
            === "string"
              ? (
                detail.message
                + " Paste the job description below instead."
              )
              : (
                "CareerCompass could not read that page. "
                + "Paste the job description below instead."
              )
          );
        }


        throw new Error(
          typeof detail
          === "string"
            ? detail
            : (
              "CareerCompass could not read that job listing."
            )
        );
      }


      const result =
        data as ManualJobPreview;


      setPreview(
        result
      );


      if (
        result.needs_description
      ) {
        setShowDescriptionFallback(
          true
        );
      }

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : (
            "CareerCompass could not read that job listing."
          )
      );

    } finally {
      setLoading(
        false
      );
    }
  }


  async function handleImport() {
    if (!preview) {
      return;
    }


    setImporting(
      true
    );

    setError(
      null
    );


    try {
      const {
        response,
        data,
      } =
        await authenticatedPost(
          "/api/manual-jobs/import",
          {
            ...requestBody(),
            preview,
          }
        );


      if (!response.ok) {
        throw new Error(
          typeof data.detail
          === "string"
            ? data.detail
            : (
              "CareerCompass could not add this role to My Applications."
            )
        );
      }


      const importResult =
        data as ManualJobImportResult;


      const {
        response: opportunityResponse,
        data: opportunityData,
      } = await authenticatedPost(
        "/api/opportunities",
        {
          job_id: importResult.job.job_id,
          source_search_request_id: null,
          priority: "medium",
          notes: null,
        }
      );


      if (!opportunityResponse.ok) {
        throw new Error(
          typeof opportunityData.detail
          === "string"
            ? opportunityData.detail
            : (
              "The listing was analysed, but CareerCompass could not save it to My Applications."
            )
        );
      }


      setImported(
        importResult
      );


      if (onOpportunitySaved) {
        void onOpportunitySaved().catch(
          () => {
            // The opportunity is already persisted. A later dashboard
            // refresh will recover if this immediate refresh fails.
          }
        );
      }

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : (
            "CareerCompass could not add this role to My Applications."
          )
      );

    } finally {
      setImporting(
        false
      );
    }
  }

  async function handleAnalyze() {
    if (!imported) {
      const message =
        "Add this role to My Applications before comparing it with your resume.";

      setError(message);
      window.alert(message);
      return;
    }


    setAnalyzing(
      true
    );

    setError(
      null
    );


    try {
      const {
        response,
        data,
      } =
        await authenticatedPost(
          (
            "/api/manual-jobs/"
            + imported.job.job_id
            + "/analyze"
          ),
          null
        );


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


      setAnalysis(
        data as ManualJobAnalysis
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : (
            "CareerCompass could not compare this role with your resume."
          )
      );

    } finally {
      setAnalyzing(
        false
      );
    }
  }




  const profileFit =
    analysis?.profile_fit
    ?? null;


  const assessedFit =
    profileFit?.status
    === "assessed"
      ? profileFit
      : null;


  const unavailableReason =
    profileFit
    && profileFit.status
      !== "assessed"
      ? profileFit.reason
      : null;


  const extractedSkills =
    preview
      ? collectSkillConcepts(
          preview.requirements
        )
      : [];


  const hardSkills =
    extractedSkills.filter(
      (concept) =>
        concept.type
        === "hard_skill"
    );


  const softSkills =
    extractedSkills.filter(
      (concept) =>
        concept.type
        === "soft_skill"
    );


  const logisticalRequirements =
    preview
      ? collectLogisticalRequirements(
          preview.requirements
        )
      : [];


  const requiredSkills =
    extractedSkills.filter(
      (concept) =>
        concept.level
        === "required"
    );


  const preferredSkills =
    extractedSkills.filter(
      (concept) =>
        concept.level
        === "preferred"
    );


  return (
    <div
      id="careercompass-manual-job-import"
      className="mt-4 scroll-mt-6"
    >

      <div className="mx-auto max-w-4xl rounded-3xl border border-white/20 bg-white/10 p-4 text-left text-slate-900 shadow-2xl backdrop-blur-md">

        <div className="rounded-3xl border border-white/20 bg-gradient-to-br from-[#0A66C2] via-[#0A66C2] to-[#004182] p-5 shadow-xl sm:p-6">

          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">

            <div>

            <p className="text-xs font-bold uppercase tracking-[0.16em] text-blue-100">
              Primary job analyser
            </p>


            <h3 className="mt-1 text-2xl font-black tracking-tight text-white">
              Analyse a job listing
            </h3>


            <p className="mt-2 max-w-2xl text-sm leading-6 text-blue-50/90">
              Analyse a job listing to extract its key requirements and compare them with your resume.
            </p>

          </div>


          <span className="w-fit rounded-full border border-white/25 bg-white/15 px-3 py-1 text-xs font-bold text-white shadow-sm backdrop-blur-sm">
            Start here
          </span>

          </div>


          <form
            onSubmit={
              handlePreview
            }
            className="mt-5 space-y-4 rounded-2xl border border-white/15 bg-white/10 p-3 shadow-inner backdrop-blur-sm sm:p-4"
          >

              <div className="grid gap-2 lg:grid-cols-[minmax(0,1fr)_auto_auto]">

                <input
                  id="careercompass-manual-job-url"
                  type="url"
                  value={
                    url
                  }
                  onChange={
                    (event) => {
                      setUrl(
                        event.target.value
                      );

                      setCameFromJobSearch(
                        false
                      );

                      setPreview(
                        null
                      );

                      resetImportedState();
                    }
                  }
                  placeholder="https://company.com/careers/job..."
                  required
                  className="min-h-12 flex-1 rounded-xl border border-white/20 bg-white px-4 py-3 text-sm text-slate-900 outline-none ring-blue-300 placeholder:text-slate-400 focus:ring-2"
                />


                <button
                  type="submit"
                  disabled={
                    loading
                  }
                  className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-bold text-[#0A66C2] shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {
                    loading
                      && (
                        <LoadingSpinner
                          label="Reading job listing"
                        />
                      )
                  }

                  {
                    loading
                      ? "Reading listing..."
                      : "Read Job Listing"
                  }
                </button>


                {
                  url.trim()
                  && (
                    <a
                      href={
                        url.trim()
                      }
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex min-h-12 items-center justify-center rounded-xl border border-white/40 bg-white/15 px-5 py-3 text-sm font-bold text-white shadow-sm transition hover:bg-white/25"
                    >
                      View Job Posting
                    </a>
                  )
                }


                <button
                  type="button"
                  onClick={
                    onResumeUpload
                  }
                  className="min-h-12 rounded-xl border border-white/40 bg-white/15 px-5 py-3 text-sm font-bold text-white shadow-sm transition hover:bg-white/25"
                >
                  Upload Resume
                </button>

              </div>


              {
                cameFromJobSearch
                && (
                  <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
                    <span className="font-bold">Job found through CareerCompass Search —</span>{" "}
                    Click <span className="font-semibold">View Job Posting</span> and paste the full job description below,
                    or find the official job listing on the company&apos;s website and paste its URL above.
                    <span className="mt-2 block text-xs italic">
                      Some job-search provider links, including Jooble listings, may not allow CareerLens to read the complete posting directly.
                    </span>
                  </div>
                )
              }


              <button
                type="button"
                onClick={() =>
                  setShowDescriptionFallback(
                    (
                      current
                    ) =>
                      !current
                  )
                }
                className="text-xs font-semibold text-blue-100 underline decoration-blue-100 underline-offset-4 hover:text-white"
              >
                Click here to paste full job description for maximum accuracy
              </button>


              {
                showDescriptionFallback
                && (
                  <textarea
                    value={
                      manualDescription
                    }
                    onChange={
                      (event) => {
                        setManualDescription(
                          event.target.value
                        );

                        setPreview(
                          null
                        );

                        resetImportedState();
                      }
                    }
                    rows={
                      8
                    }
                    placeholder="Paste the full job description here..."
                    className="w-full rounded-xl border border-white/20 bg-white px-4 py-3 text-sm leading-6 text-slate-900 outline-none ring-blue-300 placeholder:text-slate-400 focus:ring-2"
                  />
                )
              }

          </form>

        </div>


            {
              error
              && (
                <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
                  {
                    error
                  }
                </div>
              )
            }


            {
              preview
              && (
                <div className="mt-5 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">

                  <div className="flex flex-wrap items-start justify-between gap-3">

                    <div>

                      <p className="text-xs font-bold uppercase tracking-wide text-[#0A66C2]">
                        Listing found
                      </p>


                      <h4 className="mt-1 text-lg font-bold text-slate-900">
                        {
                          preview.title
                        }
                      </h4>


                      {
                        preview.company
                        && (
                          <p className="mt-1 text-sm font-medium text-slate-700">
                            {
                              preview.company
                            }
                          </p>
                        )
                      }


                      <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-600">

                        {
                          preview.location
                          && (
                            <span className="rounded-full bg-slate-100 px-2.5 py-1">
                              {
                                preview.location
                              }
                            </span>
                          )
                        }


                        {
                          preview.employment_type
                          && (
                            <span className="rounded-full bg-slate-100 px-2.5 py-1">
                              {
                                preview.employment_type
                              }
                            </span>
                          )
                        }

                      </div>

                    </div>


                    <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-[#0A66C2]">
                      {
                        preview.requirement_count
                      }{" "}
                      requirements detected
                    </span>

                  </div>


                  <p className="mt-4 text-sm leading-6 text-slate-700">
                    {
                      preview.description
                        .slice(
                          0,
                          450
                        )
                    }
                    {
                      preview.description.length
                      > 450
                        ? "..."
                        : ""
                    }
                  </p>


                  <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">

                    <div className="flex flex-wrap items-start justify-between gap-2">

                      <div>
                        <p className="text-sm font-bold text-slate-900">
                          Extracted requirements
                        </p>

                        <p className="mt-1 text-xs leading-5 text-slate-500">
                          CareerCompass separates technical skills, transferable skills and practical eligibility or commitment requirements.
                        </p>
                      </div>


                      <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-slate-600">
                        {
                          preview.requirement_count
                        }{
                          " requirements"
                        }
                      </span>

                    </div>


                    <div className="mt-4 grid gap-4 md:grid-cols-3">

                      <div className="rounded-lg border border-blue-100 bg-white p-3">
                        <p className="text-xs font-bold uppercase tracking-wide text-[#0A66C2]">
                          Hard skills
                        </p>

                        {
                          hardSkills.length
                          > 0
                            ? (
                              <div className="mt-2 flex flex-wrap gap-2">
                                {
                                  hardSkills.map(
                                    (concept) => (
                                      <span
                                        key={
                                          "hard-"
                                          + concept.name
                                        }
                                        className="rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-800"
                                      >
                                        {
                                          concept.name
                                        }
                                      </span>
                                    )
                                  )
                                }
                              </div>
                            )
                            : (
                              <p className="mt-2 text-xs text-slate-500">
                                No hard skills were confidently identified.
                              </p>
                            )
                        }
                      </div>


                      <div className="rounded-lg border border-violet-100 bg-white p-3">
                        <p className="text-xs font-bold uppercase tracking-wide text-violet-700">
                          Soft skills
                        </p>

                        {
                          softSkills.length
                          > 0
                            ? (
                              <div className="mt-2 flex flex-wrap gap-2">
                                {
                                  softSkills.map(
                                    (concept) => (
                                      <span
                                        key={
                                          "soft-"
                                          + concept.name
                                        }
                                        className="rounded-full border border-violet-200 bg-violet-50 px-2.5 py-1 text-xs font-semibold text-violet-800"
                                      >
                                        {
                                          concept.name
                                        }
                                      </span>
                                    )
                                  )
                                }
                              </div>
                            )
                            : (
                              <p className="mt-2 text-xs text-slate-500">
                                No soft skills were confidently identified.
                              </p>
                            )
                        }
                      </div>


                      <div className="rounded-lg border border-emerald-100 bg-white p-3">
                        <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">
                          Eligibility
                        </p>

                        {
                          logisticalRequirements.length
                          > 0
                            ? (
                              <div className="mt-2 space-y-2">
                                {
                                  logisticalRequirements.map(
                                    (requirement) => (
                                      <div
                                        key={
                                          "logistical-"
                                          + requirement.type
                                          + "-"
                                          + requirement.text
                                        }
                                        className="rounded-lg border border-emerald-100 bg-emerald-50/60 p-2"
                                      >
                                        <p className="text-[11px] font-bold uppercase tracking-wide text-emerald-700">
                                          {
                                            logisticalLabel(
                                              requirement.type
                                            )
                                          }
                                        </p>

                                        <p className="mt-1 text-xs leading-5 text-slate-700">
                                          {
                                            requirement.text
                                          }
                                        </p>
                                      </div>
                                    )
                                  )
                                }
                              </div>
                            )
                            : (
                              <p className="mt-2 text-xs text-slate-500">
                                No clear study-stage, commitment or eligibility requirements were identified.
                              </p>
                            )
                        }
                      </div>

                    </div>


                    {
                      (
                        requiredSkills.length
                        > 0
                        || preferredSkills.length
                        > 0
                      )
                      && (
                        <div className="mt-4 border-t border-slate-200 pt-4">

                          <p className="text-xs font-bold uppercase tracking-wide text-slate-600">
                            Requirement priority
                          </p>


                          <div className="mt-2 flex flex-wrap gap-2">

                            {
                              requiredSkills.map(
                                (concept) => (
                                  <span
                                    key={
                                      "required-"
                                      + concept.type
                                      + "-"
                                      + concept.name
                                    }
                                    className="rounded-full border border-rose-200 bg-rose-50 px-2.5 py-1 text-xs font-semibold text-rose-800"
                                  >
                                    Required · {
                                      concept.name
                                    }
                                  </span>
                                )
                              )
                            }


                            {
                              preferredSkills.map(
                                (concept) => (
                                  <span
                                    key={
                                      "preferred-"
                                      + concept.type
                                      + "-"
                                      + concept.name
                                    }
                                    className="rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-800"
                                  >
                                    Preferred · {
                                      concept.name
                                    }
                                  </span>
                                )
                              )
                            }

                          </div>

                        </div>
                      )
                    }

                  </div>


                  <div className="mt-4 flex flex-wrap gap-2">
                    {!imported && (
                      <button
                        type="button"
                        onClick={handleImport}
                        disabled={importing}
                        className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#0A66C2] px-5 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-[#004182] disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {importing && (
                          <LoadingSpinner
                            label="Adding role to My Applications"
                          />
                        )}

                        {importing
                          ? "Adding..."
                          : "Add to My Applications"}
                      </button>
                    )}

                    <button
                      type="button"
                      onClick={handleAnalyze}
                      disabled={analyzing || importing}
                      className="inline-flex items-center justify-center gap-2 rounded-lg border border-[#0A66C2] bg-white px-5 py-2.5 text-sm font-bold text-[#0A66C2] transition hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {analyzing && (
                        <LoadingSpinner
                          label="Comparing with your resume"
                        />
                      )}

                      {analyzing
                        ? "Comparing..."
                        : "Compare Resume"}
                    </button>
                  </div>


                  {imported && (
                    <div className="mt-4 rounded-xl border border-emerald-200 bg-white p-4">
                      <p className="font-semibold text-emerald-800">
                        Added to My Applications
                      </p>

                      <p className="mt-1 text-sm text-slate-600">
                        {imported.requirement_count}{" "}
                        requirements and{" "}
                        {imported.concept_link_count}{" "}
                        requirement concepts were processed.
                      </p>
                    </div>
                  )}



                  {
                    analysis
                    && analysis
                      .profile_fit
                      .status
                      !== "assessed"
                    && (
                      <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4">

                        <p className="font-semibold text-amber-900">
                          Resume comparison unavailable
                        </p>


                        <p className="mt-1 text-sm text-amber-800">
                          {
                            unavailableReason
                          }
                        </p>

                      </div>
                    )
                  }


                  {
                    assessedFit
                    && (
                      <div className="mt-4 rounded-xl border border-slate-200 bg-white p-4">

                        <div className="flex flex-wrap items-start justify-between gap-3">

                          <div>

                            <p className="text-xs font-bold uppercase tracking-wide text-[#0A66C2]">
                              Your profile vs this role
                            </p>


                            <h4 className="mt-1 text-lg font-bold text-slate-900">
                              Resume comparison
                            </h4>

                          </div>


                          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
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
                              Partially supported / needs review
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
                                    className="rounded-lg border border-slate-200 p-3"
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
                                        <div className="mt-3 space-y-2">
                                          {
                                            group
                                              .concepts
                                              .map(
                                                (
                                                  concept
                                                ) => (
                                                  <div
                                                    key={
                                                      group
                                                        .requirement_mention_id
                                                      + "-"
                                                      + concept
                                                        .concept_id
                                                    }
                                                    className="rounded-lg bg-slate-50 px-3 py-2"
                                                  >
                                                    <div className="flex flex-wrap items-center justify-between gap-2">
                                                      <span className="text-xs font-semibold text-slate-700">
                                                        {
                                                          concept.name
                                                        }
                                                      </span>

                                                      <span
                                                        className={
                                                          "rounded-full border px-2 py-0.5 text-[11px] font-semibold "
                                                          + fitClassName(
                                                              concept
                                                                .fit_status
                                                            )
                                                        }
                                                      >
                                                        {
                                                          fitLabel(
                                                            concept
                                                              .fit_status
                                                          )
                                                        }
                                                      </span>
                                                    </div>

                                                    {
                                                      concept
                                                        .model_evidence
                                                      && (
                                                        <p className="mt-2 text-xs leading-5 text-slate-600">
                                                          <span className="font-semibold text-slate-700">
                                                            Resume evidence:
                                                          </span>{" "}
                                                          “{
                                                            concept
                                                              .model_evidence
                                                          }”
                                                        </p>
                                                      )
                                                    }
                                                  </div>
                                                )
                                              )
                                          }
                                        </div>
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
                          “Not shown” means CareerCompass did not find supporting evidence in your current profile. It does not prove that you do not have the skill.
                        </p>

                      </div>
                    )
                  }

                </div>
              )
            }

      </div>

    </div>
  );
}
