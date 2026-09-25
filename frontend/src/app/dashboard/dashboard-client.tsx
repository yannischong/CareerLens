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
  CareerCompassHeader,
  type DashboardView,
} from "./career-compass-header";

import {
  ApplicationPipeline,
} from "./application-pipeline";

import {
  ApplicationResumeComparison,
} from "./application-resume-comparison";

import {
  LoadingSpinner,
} from "./loading-spinner";

type Profile = {
  profile_id: number;
  user_id: string;
  profile_name: string;
};


type Quota = {
  limit: number;
  used: number;
  remaining: number;
};


type QualityFlag = {
  flag_code: string;
  details: Record<
    string,
    unknown
  >;
};


type RequirementConcept = {
  name: string;
  type: string;
  confidence:
    number | null;
};


type Requirement = {
  id: number;
  type: string;

  level:
    | "required"
    | "preferred"
    | "unknown";

  text: string;

  structured_value:
    | Record<
        string,
        unknown
      >
    | null;

  concepts?:
    RequirementConcept[];
};


type ProfileFitConcept = {
  concept_id: number;
  name: string;
  type: string;

  level:
    | "required"
    | "preferred"
    | "unknown";

  fit_status:
    | "evidenced"
    | "claimed_only"
    | "candidate"
    | "gap";

  claim_status: string;
  evidence_status: string;
};


type ProfileFitGroupConcept = {
  concept_id: number;
  name: string;

  claim_status:
    string | null;

  evidence_status:
    string | null;

  fit_status:
    | "evidenced"
    | "claimed_only"
    | "candidate"
    | "gap"
    | null;

  model_evidence?:
    string | null;

  model_confidence?:
    number | null;
};


type ProfileFitGroup = {
  requirement_mention_id:
    number;

  type: string;

  level:
    | "required"
    | "preferred"
    | "unknown";

  text: string;

  operator:
    | "all_of"
    | "any_of";

  is_open: boolean;

  status:
    | "evidenced"
    | "claimed_only"
    | "candidate"
    | "gap"
    | "needs_review";

  explanation: string;

  matched_concept_id:
    number | null;

  matched_concept_name:
    string | null;

  concepts:
    ProfileFitGroupConcept[];
};


type UnresolvedRequirement = {
  requirement_mention_id:
    number;

  type: string;

  level:
    | "required"
    | "preferred"
    | "unknown";

  text: string;

  status:
    "needs_review";

  explanation: string;
};


type ProfileFitInsufficient = {
  status:
    "insufficient_job_data";

  model_version:
    string;

  reason:
    string;
};


type ProfileFitAssessed = {
  status:
    "assessed";

  model_version:
    string;


  /*
   * Atomic metrics.
   *
   * Retained as supporting
   * information only.
   */

  total_concepts:
    number;

  required_concepts:
    number;

  preferred_concepts:
    number;

  unknown_level_concepts:
    number;

  evidenced:
    number;

  claimed_only:
    number;

  candidate:
    number;

  gaps:
    number;

  required_candidates:
    number;

  required_gaps:
    number;


  /*
   * Logical requirement groups.
   *
   * These are the primary v2
   * Your Profile vs Role metrics.
   */

  total_groups:
    number;

  required_groups:
    number;

  preferred_groups:
    number;

  unknown_groups:
    number;

  group_evidenced:
    number;

  group_claimed_only:
    number;

  group_candidate:
    number;

  group_gaps:
    number;

  required_candidate_groups:
    number;

  required_gap_groups:
    number;

  needs_review:
    number;


  concepts:
    ProfileFitConcept[];

  groups:
    ProfileFitGroup[];

  unresolved_requirements:
    UnresolvedRequirement[];
};


type ProfileFit =
  | ProfileFitInsufficient
  | ProfileFitAssessed;


type EligibilityCheck = {
  fact_type: string;
  operator: string;

  requirement_value:
    Record<
      string,
      unknown
    >;

  requirement_text:
    string;

  status:
    | "satisfied"
    | "candidate"
    | "not_satisfied"
    | "needs_review";

  explanation:
    string;
};


type EligibilityInsufficient = {
  status:
    "insufficient_job_data";

  reason:
    string;
};


type EligibilityAssessed = {
  status:
    | "satisfied"
    | "candidate"
    | "not_satisfied"
    | "needs_review"
    | "no_explicit_checks";

  total_requirements:
    number;

  satisfied:
    number;

  candidate:
    number;

  not_satisfied:
    number;

  needs_review:
    number;

  checks:
    EligibilityCheck[];
};


type Eligibility =
  | EligibilityInsufficient
  | EligibilityAssessed;


type Job = {
  job_id:
    number;

  raw_title:
    string;

  raw_company_name:
    string;

  location_raw:
    string | null;

  employment_type:
    string | null;

  salary_text:
    string | null;

  description:
    string | null;

  job_url:
    string;

  source:
    string;

  date_posted:
    string | null;

  derived_posted_date:
    string | null;

  search_relevance:
    number | null;

  relevance_rank:
    number | null;

  provider_rank:
    number | null;

  insufficient_description:
    boolean;

  quality_flags:
    QualityFlag[];

  requirements:
    Requirement[];

  profile_fit:
    ProfileFit | null;

  eligibility:
    Eligibility | null;

  resume_match_percentage:
    number | null;

  ai_analysis_cached:
    boolean;

  analysis_method:
    string | null;

  description_source?:
    string | null;

  description_completeness?:
    "full"
    | "likely_full"
    | "partial"
    | null;

  provider_description_characters?:
    number | null;

  analysis_description_characters?:
    number | null;

  full_posting_retrieved?:
    boolean;

  original_source_url?:
    string | null;

  original_source_host?:
    string | null;

  source_resolution_method?:
    string | null;
};


type SearchResults = {
  search_request_id:
    number | null;

  count:
    number;

  jobs:
    Job[];
};


type JobTypeFilter =
  | "all"
  | "internship"
  | "full_time"
  | "part_time"
  | "contract"
  | "other";


type OpportunityStatus =
  | "discovered"
  | "saved"
  | "to_apply"
  | "applied"
  | "oa"
  | "interview"
  | "offer"
  | "rejected"
  | "withdrawn"
  | "closed";


type OpportunityPriority =
  | "low"
  | "medium"
  | "high";


type OpportunityStatusFilter =
  | "all"
  | OpportunityStatus;


type OpportunityPriorityFilter =
  | "all"
  | OpportunityPriority;


type OpportunitySort =
  | "attention"
  | "priority"
  | "deadline"
  | "stage"
  | "company"
  | "title"
  | "recent_application";


type OpportunitySummary = {
  opportunity_id:
    number;

  job_id:
    number;

  source_search_request_id:
    number | null;

  current_status:
    OpportunityStatus;

  priority:
    OpportunityPriority;

  notes:
    string | null;

  raw_title:
    string;

  raw_company_name:
    string;

  location_raw:
    string | null;

  job_url:
    string;

  source:
    string;

  search_query:
    string | null;

  application_id:
    number | null;

  resume_id:
    number | null;

  application_url:
    string | null;

  application_method:
    string | null;

  submitted_at:
    string | null;

  referral_used:
    boolean | null;

  cover_letter_used:
    boolean | null;

  application_notes:
    string | null;

  next_event_type:
    string | null;

  next_event_at:
    string | null;

  next_event_notes:
    string | null;
};


type OpportunityList = {
  count:
    number;

  opportunities:
    OpportunitySummary[];
};


type OpportunityAnalyticsCount = {
  count: number;
};


type OpportunityStatusCount =
  OpportunityAnalyticsCount
  & {
    current_status:
      OpportunityStatus;
  };


type OpportunityPriorityCount =
  OpportunityAnalyticsCount
  & {
    priority:
      OpportunityPriority;
  };


type OpportunityAnalytics = {
  tracked_opportunities:
    number;

  funnel: {
    applied: number;
    oa: number;
    interview: number;
    offer: number;
    rejected: number;
    withdrawn: number;
    responded: number;
  };

  rates: {
    application_rate_pct:
      number;

    response_rate_pct:
      number;

    oa_rate_pct:
      number;

    interview_rate_pct:
      number;

    offer_rate_pct:
      number;
  };

  timing: {
    avg_days_to_response:
      number | null;

    avg_days_to_interview:
      number | null;

    avg_days_to_offer:
      number | null;
  };

  by_status:
    OpportunityStatusCount[];

  by_priority:
    OpportunityPriorityCount[];
};


type ManualOpportunityEventType =
  | "note"
  | "deadline"
  | "follow_up"
  | "oa"
  | "interview"
  | "offer"
  | "rejection"
  | "withdrawal"
  | "other";


type OpportunityEvent = {
  event_id:
    number;

  event_type:
    string;

  from_status:
    OpportunityStatus | null;

  to_status:
    OpportunityStatus | null;

  event_at:
    string;

  notes:
    string | null;

  metadata:
    Record<string, unknown> | null;

  event_source:
    string | null;

  created_at:
    string;
};


type OpportunityDetailResponse = {
  opportunity:
    OpportunitySummary;

  events:
    OpportunityEvent[];
};


type Resume = {
  resume_id:
    number;

  original_filename:
    string;

  file_type:
    string;

  file_hash:
    string;

  parser_version:
    string;

  storage_path:
    string | null;

  uploaded_at:
    string;

  claim_count:
    number;

  evidence_count:
    number;
};


type ResumeList = {
  count:
    number;

  resumes:
    Resume[];
};


function formatText(
  value: string
) {
  return value
    .replaceAll(
      "_",
      " "
    )
    .replace(
      /\b\w/g,
      (character) =>
        character
          .toUpperCase()
    );
}


const JOB_DESCRIPTION_ENTITIES: Record<string, string> = {
  nbsp: " ",
  amp: "&",
  quot: '"',
  apos: "'",
  lt: "<",
  gt: ">",
  hellip: "…",
  ndash: "–",
  mdash: "—",
  bull: "•",
  middot: "·",
  rsquo: "’",
  lsquo: "‘",
  rdquo: "”",
  ldquo: "“",
};


function decodeJobDescriptionEntities(
  value: string
) {
  return value.replace(
    /&(#x[0-9a-f]+|#\d+|[a-z][a-z0-9]+);/gi,
    (match, entity: string) => {
      const normalized =
        entity.toLowerCase();

      if (
        normalized.startsWith(
          "#x"
        )
      ) {
        const codePoint =
          Number.parseInt(
            normalized.slice(2),
            16
          );

        return Number.isFinite(
          codePoint
        )
          ? String.fromCodePoint(
              codePoint
            )
          : " ";
      }

      if (
        normalized.startsWith(
          "#"
        )
      ) {
        const codePoint =
          Number.parseInt(
            normalized.slice(1),
            10
          );

        return Number.isFinite(
          codePoint
        )
          ? String.fromCodePoint(
              codePoint
            )
          : " ";
      }

      return (
        JOB_DESCRIPTION_ENTITIES[
          normalized
        ]
        ?? " "
      );
    }
  );
}


function cleanJobDescription(
  value: string | null
) {
  if (!value) {
    return "";
  }

  let cleaned = value;

  // Provider snippets are sometimes
  // HTML-encoded more than once.
  for (
    let pass = 0;
    pass < 3;
    pass += 1
  ) {
    cleaned =
      decodeJobDescriptionEntities(
        cleaned
      );
  }

  return cleaned
    .replace(
      /<script\b[^>]*>[\s\S]*?<\/script>/gi,
      " "
    )
    .replace(
      /<style\b[^>]*>[\s\S]*?<\/style>/gi,
      " "
    )
    .replace(
      /<!--[\s\S]*?-->/g,
      " "
    )
    .replace(
      /<br\s*\/?\s*>/gi,
      "\n"
    )
    .replace(
      /<li\b[^>]*>/gi,
      " • "
    )
    .replace(
      /<\/?(?:p|div|ul|ol|section|article|h[1-6]|tr|td|th)\b[^>]*>/gi,
      "\n"
    )
    .replace(
      /<[^>]*>/g,
      " "
    )
    .replace(
      /\u00a0/g,
      " "
    )
    .replace(
      /[ \t\f\v]+/g,
      " "
    )
    .replace(
      / *\n */g,
      "\n"
    )
    .replace(
      /\n{2,}/g,
      "\n"
    )
    .replace(
      /\s+([,.;:!?])/g,
      "$1"
    )
    .replace(
      /\.\s*\.\s*\./g,
      "…"
    )
    .replace(
      /^(?:…|\.{2,})\s*/,
      ""
    )
    .trim();
}


function formatDateTime(
  value: string
) {
  return new Date(
    value
  ).toLocaleString();
}


function getLocalDateTimeInputValue() {
  const now = new Date();

  const local = new Date(
    now.getTime()
    - now.getTimezoneOffset()
      * 60_000
  );

  return local
    .toISOString()
    .slice(0, 16);
}


type SkillGapCoverage = {
  total_search_jobs: number;

  sufficient_description_jobs:
    number;

  insufficient_description_jobs:
    number;

  jobs_with_requirement_groups:
    number;

  analyzed_job_count:
    number;

  excluded_low_quality_jobs:
    number;

  overall_coverage_pct:
    number;

  sufficient_description_coverage_pct:
    number;
};


type SkillGapExample = {
  job_id: number;

  raw_title: string;

  requirement_mention_id:
    number;

  requirement_level:
    | "required"
    | "preferred"
    | "unknown";

  group_operator:
    | "all_of"
    | "any_of";

  group_is_open:
    boolean;

  requirement_text:
    string;
};


type SkillGapPriority = {
  priority_rank: number;

  priority_tier:
    | "A"
    | "B"
    | "C"
    | "D";

  priority_label:
    string;

  priority_reason:
    string;

  next_step:
    string;

  family_name:
    string;

  source_concepts:
    string[];

  concept_types:
    string[];

  gap_job_count:
    number;

  gap_job_share_pct:
    number;

  gap_weight:
    number;

  required_gap_groups:
    number;

  preferred_gap_groups:
    number;

  unknown_gap_groups:
    number;

  examples:
    SkillGapExample[];
};


type SkillGapResponse = {
  profile_id:
    number;

  search_request_id:
    number;

  query_text:
    string;

  location_text:
    string;

  country_code:
    string;

  coverage:
    SkillGapCoverage;

  tier_counts: {
    A: number;
    B: number;
    C: number;
    D: number;
  };

  priority_count:
    number;

  priorities:
    SkillGapPriority[];
};


type SkillGapPanelProps = {
  refreshKey:
    string;
};


function getSkillGapTierClass(
  tier:
    SkillGapPriority[
      "priority_tier"
    ]
) {
  if (tier === "A") {
    return (
      "border-red-200 "
      + "bg-red-50 "
      + "text-red-800"
    );
  }


  if (tier === "B") {
    return (
      "border-orange-200 "
      + "bg-orange-50 "
      + "text-orange-800"
    );
  }


  if (tier === "C") {
    return (
      "border-blue-200 "
      + "bg-blue-50 "
      + "text-blue-800"
    );
  }


  return (
    "border-gray-200 "
    + "bg-gray-50 "
    + "text-gray-700"
  );
}


function getSkillGapTierHeading(
  tier:
    SkillGapPriority[
      "priority_tier"
    ]
) {
  if (tier === "A") {
    return (
      "Common gaps across roles"
    );
  }


  if (tier === "B") {
    return (
      "Required in a specific role"
    );
  }


  if (tier === "C") {
    return (
      "Worth reviewing"
    );
  }


  return (
    "Nice-to-have skills"
  );
}


function getSkillGapTierLabel(
  tier:
    SkillGapPriority[
      "priority_tier"
    ]
) {
  if (tier === "A") {
    return "High priority";
  }


  if (tier === "B") {
    return "Required";
  }


  if (tier === "C") {
    return "Review";
  }


  return "Optional";
}


function getOpportunityStatusClass(
  status:
    OpportunityStatus
) {
  if (
    status === "offer"
  ) {
    return (
      "bg-emerald-100 "
      + "text-emerald-800"
    );
  }


  if (
    status === "interview"
  ) {
    return (
      "bg-violet-100 "
      + "text-violet-800"
    );
  }


  if (
    status === "oa"
  ) {
    return (
      "bg-indigo-100 "
      + "text-indigo-800"
    );
  }


  if (
    status === "applied"
  ) {
    return (
      "bg-sky-100 "
      + "text-sky-800"
    );
  }


  if (
    status === "to_apply"
  ) {
    return (
      "bg-amber-100 "
      + "text-amber-800"
    );
  }


  if (
    status === "rejected"
  ) {
    return (
      "bg-rose-100 "
      + "text-rose-800"
    );
  }


  if (
    status === "withdrawn"
    || status === "closed"
  ) {
    return (
      "bg-slate-100 "
      + "text-slate-700"
    );
  }


  return (
    "bg-blue-100 "
    + "text-blue-800"
  );
}


function getOpportunityPriorityClass(
  priority:
    OpportunityPriority
) {
  if (priority === "high") {
    return (
      "bg-red-50 "
      + "text-red-800"
    );
  }


  if (priority === "low") {
    return (
      "bg-gray-100 "
      + "text-gray-700"
    );
  }


  return (
    "bg-blue-50 "
    + "text-blue-800"
  );
}


function classifyJobType(
  job: Job
): Exclude<
  JobTypeFilter,
  "all"
> {
  const text =
    [
      job.raw_title,
      job.employment_type,
      job.description,
    ]
      .filter(
        (
          value
        ) => Boolean(
          value
        )
      )
      .join(" ")
      .toLowerCase();


  if (
    /\bintern(ship)?\b/.test(
      text
    )
    || /\btrainee\b/.test(
      text
    )
  ) {
    return "internship";
  }


  if (
    /\bpart[- ]?time\b/.test(
      text
    )
  ) {
    return "part_time";
  }


  if (
    /\bcontract(or)?\b/.test(
      text
    )
    || /\btemporary\b/.test(
      text
    )
    || /\btemp\b/.test(
      text
    )
  ) {
    return "contract";
  }


  if (
    /\bfull[- ]?time\b/.test(
      text
    )
    || /\bpermanent\b/.test(
      text
    )
  ) {
    return "full_time";
  }


  return "other";
}


function extractExplicitJobStartMonth(
  job: Job
) {
  const text =
    [
      job.raw_title,
      job.description,
    ]
      .filter(
        (
          value
        ) => Boolean(
          value
        )
      )
      .join(" ")
      .replaceAll(
        "\n",
        " "
      );


  const monthNames =
    "January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec";


  const patterns = [
    new RegExp(
      `(?:start(?:ing)?|commenc(?:e|ing)|begin(?:ning)?|intake|internship\\s+period|from)\\s*(?:date)?\\s*[:\\-]?\\s*[^.!?]{0,35}?\\b(${monthNames})\\s+(20\\d{2})\\b`,
      "i"
    ),

    new RegExp(
      `\\b(${monthNames})\\s+(20\\d{2})\\b[^.!?]{0,35}?(?:start|starting|commence|commencing|intake)`,
      "i"
    ),
  ];


  const monthLookup:
    Record<
      string,
      number
    > = {
      january: 1,
      jan: 1,
      february: 2,
      feb: 2,
      march: 3,
      mar: 3,
      april: 4,
      apr: 4,
      may: 5,
      june: 6,
      jun: 6,
      july: 7,
      jul: 7,
      august: 8,
      aug: 8,
      september: 9,
      sep: 9,
      sept: 9,
      october: 10,
      oct: 10,
      november: 11,
      nov: 11,
      december: 12,
      dec: 12,
    };


  for (
    const pattern
    of patterns
  ) {
    const match =
      text.match(
        pattern
      );


    if (!match) {
      continue;
    }


    const month =
      monthLookup[
        match[1]
          .toLowerCase()
      ];

    const year =
      Number(
        match[2]
      );


    if (
      !month
      || !year
    ) {
      continue;
    }


    return (
      `${year}-`
      + `${month}`
        .padStart(
          2,
          "0"
        )
    );
  }


  return null;
}


function formatStartMonth(
  value: string
) {
  const [
    year,
    month,
  ] = value
    .split("-")
    .map(
      Number
    );


  return new Intl.DateTimeFormat(
    "en-SG",
    {
      month:
        "long",

      year:
        "numeric",
    }
  ).format(
    new Date(
      year,
      month - 1,
      1
    )
  );
}


function SkillGapPanel({
  refreshKey,
}: SkillGapPanelProps) {
  const [
    analysis,
    setAnalysis,
  ] = useState<
    SkillGapResponse | null
  >(null);


  const [
    loading,
    setLoading,
  ] = useState(
    true
  );


  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);


  useEffect(() => {
    async function loadSkillGaps() {
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
        session?.access_token;


      if (!token) {
        setError(
          "No authenticated session."
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
            `${apiUrl}/api/analytics/latest/skill-gaps`,
            {
              headers: {
                Authorization:
                  `Bearer ${token}`,
              },

              cache:
                "no-store",
            }
          );


        if (
          response.status === 404
        ) {
          setAnalysis(
            null
          );

          return;
        }


        if (
          !response.ok
        ) {
          throw new Error(
            "Failed to load skill gap intelligence"
          );
        }


        const data:
          SkillGapResponse =
            await response.json();


        setAnalysis(
          data
        );

      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : (
              "Failed to load "
              + "skill gap intelligence"
            )
        );

      } finally {
        setLoading(
          false
        );
      }
    }


    loadSkillGaps();

  }, [
    refreshKey,
  ]);


  if (loading) {
    return (
      <section
        className={
          "rounded-xl bg-white "
          + "p-6 shadow-sm"
        }
      >
        <h2
          className={
            "text-xl "
            + "font-semibold"
          }
        >
          Skill Trends
        </h2>

        <div
          className={
            "mt-3 flex items-center gap-2 "
            + "text-sm text-gray-500"
          }
        >
          <LoadingSpinner
            label="Analysing skill trends"
          />

          <span>
            Analysing profile support
            across job requirements...
          </span>
        </div>
      </section>
    );
  }


  if (error) {
    return (
      <section
        className={
          "rounded-xl bg-white "
          + "p-6 shadow-sm"
        }
      >
        <h2
          className={
            "text-xl "
            + "font-semibold"
          }
        >
          Skill Trends
        </h2>

        <p
          className={
            "mt-2 text-sm "
            + "text-red-600"
          }
        >
          {error}
        </p>
      </section>
    );
  }


  if (!analysis) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-slate-900">
          Career Insights
        </h2>

        <p className="mt-2 text-sm text-slate-600">
          Career insights are generated from the roles returned by your latest job search.
        </p>

        <button
          type="button"
          onClick={() => {
            const searchPanel =
              document.getElementById(
                "careercompass-search"
              ) as HTMLDetailsElement | null;

            if (searchPanel) {
              searchPanel.open =
                true;
            }

            searchPanel
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
          }}
          className="mt-4 text-left text-sm font-semibold text-[#0A66C2] underline decoration-blue-300 underline-offset-4 transition hover:text-[#004182]"
        >
          Search a desired role to view Career Insights.
        </button>
      </section>
    );
  }


  const coverage =
    analysis.coverage;


  const tierA =
    analysis.priorities.filter(
      (gap) =>
        gap.priority_tier === "A"
    );


  const tierB =
    analysis.priorities.filter(
      (gap) =>
        gap.priority_tier === "B"
    );


  const tierC =
    analysis.priorities.filter(
      (gap) =>
        gap.priority_tier === "C"
    );


  const tierD =
    analysis.priorities.filter(
      (gap) =>
        gap.priority_tier === "D"
    );


  function renderGap(
    gap:
      SkillGapPriority
  ) {
    return (
      <div
        key={
          `${gap.priority_tier}-`
          + `${gap.family_name}`
        }
        className={
          "rounded-xl border "
          + "border-slate-200 "
          + "bg-white p-4 "
          + "shadow-sm"
        }
      >
        <div
          className={
            "flex flex-wrap "
            + "items-start "
            + "justify-between "
            + "gap-3"
          }
        >
          <div>
            <h4
              className={
                "font-medium "
                + "text-gray-900"
              }
            >
              {gap.family_name}
            </h4>

            <p
              className={
                "mt-1 text-sm "
                + "text-gray-600"
              }
            >
              This skill is not currently supported by confirmed evidence in your uploaded resume.
            </p>
          </div>

          <span
            className={
              "rounded-full "
              + "border px-2.5 "
              + "py-1 text-xs "
              + "font-medium "
              + getSkillGapTierClass(
                gap.priority_tier
              )
            }
          >
            {
              getSkillGapTierLabel(
                gap.priority_tier
              )
            }
          </span>
        </div>


        <div
          className={
            "mt-3 flex "
            + "flex-wrap gap-4 "
            + "text-sm "
            + "text-gray-700"
          }
        >
          <span>
            <strong>
              {
                gap
                  .gap_job_count
              }
            </strong>
            {" / "}
            {
              coverage
                .analyzed_job_count
            }
            {" jobs"}
          </span>

          <span>
            {
              gap
                .gap_job_share_pct
            }
            % of analyzed jobs
          </span>
        </div>


        {(
          gap.source_concepts
            .length > 1
        ) && (
          <p
            className={
              "mt-3 text-xs "
              + "text-gray-500"
            }
          >
            Grouped from:{" "}
            {
              gap.source_concepts
                .join(", ")
            }
          </p>
        )}


        {(
          gap.examples
            .length > 0
        ) && (
          <details
            className="mt-3"
          >
            <summary
              className={
                "cursor-pointer "
                + "text-sm "
                + "font-medium "
                + "text-gray-700"
              }
            >
              See why this appears
            </summary>

            <div
              className={
                "mt-2 space-y-2"
              }
            >
              {
                gap.examples
                  .slice(
                    0,
                    2
                  )
                  .map(
                    (
                      example
                    ) => (
                      <div
                        key={
                          example
                            .requirement_mention_id
                        }
                        className={
                          "rounded "
                          + "bg-gray-50 "
                          + "p-3 text-sm"
                        }
                      >
                        <p
                          className={
                            "font-medium "
                            + "text-gray-800"
                          }
                        >
                          {
                            example
                              .raw_title
                          }
                        </p>

                        <p
                          className={
                            "mt-1 "
                            + "text-gray-600"
                          }
                        >
                          {
                            example
                              .requirement_text
                          }
                        </p>
                      </div>
                    )
                  )
              }
            </div>
          </details>
        )}
      </div>
    );
  }


  function renderTier(
    tier:
      SkillGapPriority[
        "priority_tier"
      ],

    gaps:
      SkillGapPriority[],

    expanded:
      boolean
  ) {
    if (
      gaps.length === 0
    ) {
      return null;
    }


    if (expanded) {
      return (
        <div
          className={
            "space-y-3"
          }
        >
          <h3
            className={
              "text-sm "
              + "font-semibold "
              + "uppercase "
              + "tracking-wide "
              + "text-gray-600"
            }
          >
            {
              getSkillGapTierHeading(
                tier
              )
            }
          </h3>

          {
            gaps.map(
              renderGap
            )
          }
        </div>
      );
    }


    return (
      <details
        className={
          "rounded-lg border "
          + "bg-gray-50 p-4"
        }
      >
        <summary
          className={
            "cursor-pointer "
            + "font-medium "
            + "text-gray-800"
          }
        >
          {
            getSkillGapTierHeading(
              tier
            )
          }
          {" ("}
          {gaps.length}
          {")"}
        </summary>

        <div
          className={
            "mt-4 space-y-3"
          }
        >
          {
            gaps.map(
              renderGap
            )
          }
        </div>
      </details>
    );
  }


  return (
    <section
      className={
        "rounded-2xl border "
        + "border-slate-200 bg-white "
        + "p-6 shadow-sm"
      }
    >
      <div
        className={
          "flex flex-wrap "
          + "items-start "
          + "justify-between "
          + "gap-4"
        }
      >
        <div>
          <h2
            className={
              "text-xl "
              + "font-semibold"
            }
          >
            Skills to Build
          </h2>

          <p
            className={
              "mt-1 text-sm "
              + "text-gray-600"
            }
          >
            See which skills repeatedly appear in your latest{" "}
            <strong>
              {analysis.query_text}
            </strong>
            {" "}
            search but are not yet supported by your uploaded resume.
          </p>
        </div>

        <div
          className={
            "rounded-lg "
            + "bg-gray-50 "
            + "px-4 py-2 "
            + "text-right"
          }
        >
          <p
            className={
              "text-sm "
              + "font-semibold"
            }
          >
            {
              coverage
                .analyzed_job_count
            }
            {" / "}
            {
              coverage
                .sufficient_description_jobs
            }
          </p>

          <p
            className={
              "text-xs "
              + "text-gray-500"
            }
          >
            usable job descriptions analyzed
          </p>
        </div>
      </div>


      <div
        className={
          "mt-4 rounded-lg "
          + "border border-amber-200 "
          + "bg-amber-50 p-4 "
          + "text-sm "
          + "text-amber-900"
        }
      >
        <p
          className="font-medium"
        >
          How reliable is this insight?
        </p>

        <p className="mt-1">
          CareerCompass analyzed{" "}
          {
            coverage
              .analyzed_job_count
          }
          {" of "}
          {
            coverage
              .total_search_jobs
          }
          {" search results ("}
          {
            coverage
              .overall_coverage_pct
          }
          % overall).
          {" "}
          {
            coverage
              .insufficient_description_jobs
          }
          {" jobs had descriptions "}
          too limited for reliable
          cross-job gap analysis.
        </p>

        <p className="mt-2">
          Among jobs with sufficient
          description data, coverage
          was{" "}
          {
            coverage
              .sufficient_description_coverage_pct
          }
          %.
        </p>
      </div>


      <div
        className={
          "mt-4 rounded-lg "
          + "bg-blue-50 p-4 "
          + "text-sm "
          + "text-blue-900"
        }
      >
        These insights only reflect what CareerCompass can verify from your uploaded resume. A skill shown here may still be something you have but have not included on your resume yet.
      </div>


      <div
        className={
          "mt-6 space-y-6"
        }
      >
        {
          renderTier(
            "A",
            tierA,
            true
          )
        }

        {
          renderTier(
            "B",
            tierB,
            true
          )
        }

        {
          renderTier(
            "C",
            tierC,
            false
          )
        }

        {
          renderTier(
            "D",
            tierD,
            false
          )
        }
      </div>
    </section>
  );
}


type DashboardClientProps = {
  userEmail: string;
};


export default function DashboardClient({
  userEmail,
}: DashboardClientProps) {
  const [
    ,
    setProfile,
  ] =
    useState<
      Profile | null
    >(null);


  const [
    quota,
    setQuota,
  ] =
    useState<
      Quota | null
    >(null);


  const [
    jobs,
    setJobs,
  ] =
    useState<Job[]>(
      []
    );


  const [
    resumes,
    setResumes,
  ] =
    useState<
      Resume[]
    >([]);


  const [
    opportunities,
    setOpportunities,
  ] =
    useState<
      OpportunitySummary[]
    >([]);


  const [
    opportunityAnalytics,
    setOpportunityAnalytics,
  ] =
    useState<
      OpportunityAnalytics | null
    >(null);


  const [
    currentSearchRequestId,
    setCurrentSearchRequestId,
  ] =
    useState<
      number | null
    >(null);


  const [
    trackingJobId,
    setTrackingJobId,
  ] =
    useState<
      number | null
    >(null);


  const [
    updatingOpportunityId,
    setUpdatingOpportunityId,
  ] =
    useState<
      number | null
    >(null);


  const [
    deletingOpportunityId,
    setDeletingOpportunityId,
  ] =
    useState<
      number | null
    >(null);


  const [
    editingOpportunityId,
    setEditingOpportunityId,
  ] =
    useState<
      number | null
    >(null);


  const [
    editingApplicationOpportunityId,
    setEditingApplicationOpportunityId,
  ] =
    useState<
      number | null
    >(null);


  const [
    historyOpportunityId,
    setHistoryOpportunityId,
  ] =
    useState<
      number | null
    >(null);


  const [
    loadingHistoryOpportunityId,
    setLoadingHistoryOpportunityId,
  ] =
    useState<
      number | null
    >(null);


  const [
    opportunityEvents,
    setOpportunityEvents,
  ] =
    useState<
      Record<
        number,
        OpportunityEvent[]
      >
    >({});


  const [
    addingEventOpportunityId,
    setAddingEventOpportunityId,
  ] =
    useState<
      number | null
    >(null);


  const [
    savingEventOpportunityId,
    setSavingEventOpportunityId,
  ] =
    useState<
      number | null
    >(null);


  const [
    newEventType,
    setNewEventType,
  ] =
    useState<
      ManualOpportunityEventType
    >("note");


  const [
    newEventAt,
    setNewEventAt,
  ] =
    useState("");


  const [
    newEventNotes,
    setNewEventNotes,
  ] =
    useState("");


  const [
    activeView,
    setActiveView,
  ] =
    useState<
      DashboardView
    >("jobs");


  const [
    opportunitySearch,
    setOpportunitySearch,
  ] =
    useState("");


  const [
    opportunityStatusFilter,
    setOpportunityStatusFilter,
  ] =
    useState<
      OpportunityStatusFilter
    >("all");


  const [
    opportunityPriorityFilter,
    setOpportunityPriorityFilter,
  ] =
    useState<
      OpportunityPriorityFilter
    >("all");


  const [
    opportunitySort,
    setOpportunitySort,
  ] =
    useState<
      OpportunitySort
    >("attention");


  const [
    jobTypeFilter,
    setJobTypeFilter,
  ] =
    useState<
      JobTypeFilter
    >("all");


  const [
    jobStartMonthFilter,
    setJobStartMonthFilter,
  ] =
    useState(
      "all"
    );


  const [
    query,
    setQuery,
  ] =
    useState("");


  const [
    location,
    setLocation,
  ] =
    useState(
      "Singapore"
    );


  const [
    searching,
    setSearching,
  ] =
    useState(false);


  const [
    uploading,
    setUploading,
  ] =
    useState(false);


  const [
    selectedFile,
    setSelectedFile,
  ] =
    useState<
      File | null
    >(null);


  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);


  const [
    resumeMessage,
    setResumeMessage,
  ] =
    useState<
      string | null
    >(null);


  const [
    loading,
    setLoading,
  ] =
    useState(true);


  async function getAccessToken() {
    const supabase =
      createClient();


    const {
      data: {
        session,
      },
    } =
      await supabase
        .auth
        .getSession();


    return (
      session
        ?.access_token
      ?? null
    );
  }


  async function loadResumes(
    token: string
  ) {
    const apiUrl =
      process.env
        .NEXT_PUBLIC_API_URL;


    const response =
      await fetch(
        `${apiUrl}/api/resumes`,
        {
          headers: {
            Authorization:
              `Bearer ${token}`,
          },
        }
      );


    if (
      !response.ok
    ) {
      throw new Error(
        "Failed to load resumes"
      );
    }


    const data:
      ResumeList =
        await response.json();


    setResumes(
      data.resumes
    );
  }


  async function loadOpportunities(
    token: string
  ) {
    const apiUrl =
      process.env
        .NEXT_PUBLIC_API_URL;


    const response =
      await fetch(
        `${apiUrl}/api/opportunities`,
        {
          headers: {
            Authorization:
              `Bearer ${token}`,
          },

          cache:
            "no-store",
        }
      );


    if (
      !response.ok
    ) {
      throw new Error(
        "Failed to load tracked opportunities"
      );
    }


    const data:
      OpportunityList =
        await response.json();


    setOpportunities(
      data.opportunities
    );
  }


  async function loadOpportunityAnalytics(
    token: string
  ) {
    const apiUrl =
      process.env
        .NEXT_PUBLIC_API_URL;


    const response =
      await fetch(
        `${apiUrl}/api/opportunities/analytics`,
        {
          headers: {
            Authorization:
              `Bearer ${token}`,
          },

          cache:
            "no-store",
        }
      );


    if (
      !response.ok
    ) {
      throw new Error(
        "Failed to load application analytics"
      );
    }


    const data:
      OpportunityAnalytics =
        await response.json();


    setOpportunityAnalytics(
      data
    );
  }


  async function handleManualOpportunitySaved() {
    const token =
      await getAccessToken();


    if (!token) {
      throw new Error(
        "Your session has expired."
      );
    }


    await Promise.all([
      loadOpportunities(
        token
      ),

      loadOpportunityAnalytics(
        token
      ),
    ]);
  }


  async function loadLatestResults(
    token: string
  ) {
    const apiUrl =
      process.env
        .NEXT_PUBLIC_API_URL;


    const response =
      await fetch(
        `${apiUrl}/api/search/latest/results`,
        {
          headers: {
            Authorization:
              `Bearer ${token}`,
          },
        }
      );


    if (
      !response.ok
    ) {
      throw new Error(
        "Failed to load latest results"
      );
    }


    const data:
      SearchResults =
        await response.json();


    setCurrentSearchRequestId(
      data.search_request_id
    );


    setJobs(
      data.jobs
    );
  }


  async function loadResults(
    searchRequestId:
      number,

    token:
      string
  ) {
    const apiUrl =
      process.env
        .NEXT_PUBLIC_API_URL;


    const response =
      await fetch(
        `${apiUrl}/api/search/${searchRequestId}/results`,
        {
          headers: {
            Authorization:
              `Bearer ${token}`,
          },
        }
      );


    if (
      !response.ok
    ) {
      throw new Error(
        "Failed to load job results"
      );
    }


    const data:
      SearchResults =
        await response.json();


    setCurrentSearchRequestId(
      data.search_request_id
      ?? searchRequestId
    );


    setJobs(
      data.jobs
    );
  }


  function sendJobToAnalyser(
    job: Job
  ) {
    window.dispatchEvent(
      new CustomEvent(
        "careerlens:analyse-search-job",
        {
          detail: {
            title:
              job.raw_title,

            company:
              job.raw_company_name,

            location:
              job.location_raw,

            sourceUrl:
              job.job_url,

            source:
              job.source,
          },
        }
      )
    );


    window.setTimeout(
      () => {
        document
          .getElementById(
            "careercompass-manual-job-import"
          )
          ?.scrollIntoView({
            behavior:
              "smooth",

            block:
              "start",
          });


        window.setTimeout(
          () => {
            document
              .getElementById(
                "careercompass-manual-job-url"
              )
              ?.focus();
          },
          500
        );
      },
      50
    );
  }


  useEffect(() => {
    async function loadDashboard() {
      const token =
        await getAccessToken();


      if (!token) {
        setError(
          "No authenticated session."
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
        const profileResponse =
          await fetch(
            `${apiUrl}/api/me`,
            {
              headers: {
                Authorization:
                  `Bearer ${token}`,
              },
            }
          );


        if (
          !profileResponse.ok
        ) {
          throw new Error(
            "Failed to load CareerCompass profile"
          );
        }


        setProfile(
          await profileResponse
            .json()
        );


        const quotaResponse =
          await fetch(
            `${apiUrl}/api/search/quota`,
            {
              headers: {
                Authorization:
                  `Bearer ${token}`,
              },
            }
          );


        if (
          !quotaResponse.ok
        ) {
          throw new Error(
            "Failed to load search quota"
          );
        }


        setQuota(
          await quotaResponse
            .json()
        );


        await loadLatestResults(
          token
        );


        await loadResumes(
          token
        );


        await loadOpportunities(
          token
        );


        await loadOpportunityAnalytics(
          token
        );

      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : (
              "Something "
              + "went wrong"
            )
        );

      } finally {
        setLoading(
          false
        );
      }
    }


    loadDashboard();

  }, []);


  async function handleResumeUpload(
    event:
      FormEvent<
        HTMLFormElement
      >
  ) {
    event.preventDefault();


    if (
      !selectedFile
    ) {
      setError(
        "Choose a resume file first."
      );

      return;
    }


    setUploading(
      true
    );

    setError(
      null
    );

    setResumeMessage(
      null
    );


    const token =
      await getAccessToken();


    if (!token) {
      setError(
        "Your session has expired."
      );

      setUploading(
        false
      );

      return;
    }


    const apiUrl =
      process.env
        .NEXT_PUBLIC_API_URL;


    const formData =
      new FormData();


    formData.append(
      "file",
      selectedFile
    );


    try {
      const response =
        await fetch(
          `${apiUrl}/api/resumes`,
          {
            method:
              "POST",

            headers: {
              Authorization:
                `Bearer ${token}`,
            },

            body:
              formData,
          }
        );


      const data =
        await response
          .json();


      if (
        !response.ok
      ) {
        throw new Error(
          typeof data.detail
            === "string"

            ? data.detail

            : (
              "Resume "
              + "upload failed"
            )
        );
      }


      setResumeMessage(
        (
          data.replaced
            ? "Resume replaced. "
            : "Resume uploaded. "
        )
        + `${data.resume.claims} `
        + `profile points and `
        + `${data.resume.evidence} `
        + `supporting details were processed.`
      );


      setSelectedFile(
        null
      );


      await loadResumes(
        token
      );


      await loadLatestResults(
        token
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : (
            "Resume "
            + "upload failed"
          )
      );

    } finally {
      setUploading(
        false
      );
    }
  }


  async function handleSearch(
    event:
      FormEvent<
        HTMLFormElement
      >
  ) {
    event.preventDefault();


    if (
      !query.trim()
    ) {
      return;
    }


    setSearching(
      true
    );

    setError(
      null
    );


    const token =
      await getAccessToken();


    if (!token) {
      setError(
        "Your session has expired."
      );

      setSearching(
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
          `${apiUrl}/api/search`,
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
              JSON.stringify({
                query:
                  query.trim(),

                location:
                  location.trim(),

                country:
                  "sg",

                providers: [
                  "serpapi",
                  "jooble",
                ],

                pages:
                  1,
              }),
          }
        );


      const data =
        await response
          .json();


      if (
        !response.ok
      ) {
        if (
          response.status
          === 429
        ) {
          throw new Error(
            "You have used both "
            + "of your available "
            + "job searches."
          );
        }


        throw new Error(
          typeof data.detail
            === "string"

            ? data.detail

            : "Job search failed"
        );
      }


      setQuota(
        data.quota
      );


      await loadResults(
        data.search
          .search_request_id,

        token
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Job search failed"
      );

    } finally {
      setSearching(
        false
      );
    }
  }


  async function handleTrackJob(
    jobId: number
  ) {
    setTrackingJobId(
      jobId
    );

    setError(
      null
    );


    const token =
      await getAccessToken();


    if (!token) {
      setError(
        "Your session has expired."
      );

      setTrackingJobId(
        null
      );

      return;
    }


    const apiUrl =
      process.env
        .NEXT_PUBLIC_API_URL;


    try {
      const response =
        await fetch(
          `${apiUrl}/api/opportunities`,
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
              JSON.stringify({
                job_id:
                  jobId,

                source_search_request_id:
                  currentSearchRequestId,

                priority:
                  "medium",

                notes:
                  null,
              }),
          }
        );


      const data =
        await response.json();


      if (
        !response.ok
      ) {
        throw new Error(
          typeof data.detail
            === "string"

            ? data.detail

            : (
              "Failed to track "
              + "opportunity"
            )
        );
      }


      await loadOpportunities(
        token
      );


      await loadOpportunityAnalytics(
        token
      );


      setEditingOpportunityId(
        null
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : (
            "Failed to track "
            + "opportunity"
          )
      );

    } finally {
      setTrackingJobId(
        null
      );
    }
  }


  function getTrackedOpportunity(
    jobId: number
  ) {
    return opportunities.find(
      (opportunity) =>
        opportunity.job_id
        === jobId
    ) ?? null;
  }


  async function toggleOpportunityHistory(
    opportunityId: number
  ) {
    if (
      historyOpportunityId
      === opportunityId
    ) {
      setHistoryOpportunityId(
        null
      );

      return;
    }


    setEditingOpportunityId(
      null
    );

    setEditingApplicationOpportunityId(
      null
    );

    setAddingEventOpportunityId(
      null
    );

    setHistoryOpportunityId(
      opportunityId
    );

    setLoadingHistoryOpportunityId(
      opportunityId
    );

    setError(
      null
    );


    const token =
      await getAccessToken();


    if (!token) {
      setError(
        "Your session has expired."
      );

      setHistoryOpportunityId(
        null
      );

      setLoadingHistoryOpportunityId(
        null
      );

      return;
    }


    const apiUrl =
      process.env
        .NEXT_PUBLIC_API_URL;


    try {
      const response =
        await fetch(
          `${apiUrl}/api/opportunities/${opportunityId}`,
          {
            headers: {
              Authorization:
                `Bearer ${token}`,
            },

            cache:
              "no-store",
          }
        );


      const data:
        OpportunityDetailResponse =
          await response.json();


      if (
        !response.ok
      ) {
        throw new Error(
          "Failed to load opportunity history"
        );
      }


      setOpportunityEvents(
        (
          current
        ) => ({
          ...current,

          [opportunityId]:
            data.events,
        })
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : (
            "Failed to load "
            + "opportunity history"
          )
      );

      setHistoryOpportunityId(
        null
      );

    } finally {
      setLoadingHistoryOpportunityId(
        null
      );
    }
  }


  function updateNewEventType(
    value: string
  ) {
    if (
      value !== "note"
      && value !== "deadline"
      && value !== "follow_up"
      && value !== "oa"
      && value !== "interview"
      && value !== "offer"
      && value !== "rejection"
      && value !== "withdrawal"
      && value !== "other"
    ) {
      return;
    }

    setNewEventType(
      value
    );
  }


  function toggleAddOpportunityEvent(
    opportunityId: number
  ) {
    if (
      addingEventOpportunityId
      === opportunityId
    ) {
      setAddingEventOpportunityId(
        null
      );

      return;
    }


    setEditingOpportunityId(
      null
    );

    setEditingApplicationOpportunityId(
      null
    );

    setHistoryOpportunityId(
      null
    );

    setAddingEventOpportunityId(
      opportunityId
    );

    setNewEventType(
      "note"
    );

    setNewEventAt(
      getLocalDateTimeInputValue()
    );

    setNewEventNotes(
      ""
    );
  }


  async function handleAddOpportunityEvent(
    event: FormEvent<
      HTMLFormElement
    >,
    opportunityId: number
  ) {
    event.preventDefault();

    setSavingEventOpportunityId(
      opportunityId
    );

    setError(
      null
    );


    const token =
      await getAccessToken();


    if (!token) {
      setError(
        "Your session has expired."
      );

      setSavingEventOpportunityId(
        null
      );

      return;
    }


    const apiUrl =
      process.env
        .NEXT_PUBLIC_API_URL;


    try {
      const response =
        await fetch(
          `${apiUrl}/api/opportunities/${opportunityId}/events`,
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
              JSON.stringify({
                event_type:
                  newEventType,

                event_at:
                  newEventAt
                    ? new Date(
                        newEventAt
                      ).toISOString()
                    : null,

                notes:
                  newEventNotes.trim()
                    || null,
              }),
          }
        );


      const data =
        await response.json();


      if (
        !response.ok
      ) {
        throw new Error(
          typeof data.detail
            === "string"

            ? data.detail

            : (
              "Failed to add "
              + "opportunity event"
            )
        );
      }


      setOpportunityEvents(
        (
          current
        ) => ({
          ...current,

          [opportunityId]: [
            ...(
              current[
                opportunityId
              ]
              ?? []
            ),

            data.event,
          ],
        })
      );


      await loadOpportunityAnalytics(
        token
      );


      setAddingEventOpportunityId(
        null
      );

      setHistoryOpportunityId(
        opportunityId
      );

      setNewEventNotes(
        ""
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : (
            "Failed to add "
            + "opportunity event"
          )
      );

    } finally {
      setSavingEventOpportunityId(
        null
      );
    }
  }


  function updateOpportunityStatusDraft(
    opportunityId: number,
    value: string
  ) {
    if (
      value !== "discovered"
      && value !== "saved"
      && value !== "to_apply"
      && value !== "applied"
      && value !== "oa"
      && value !== "interview"
      && value !== "offer"
      && value !== "rejected"
      && value !== "withdrawn"
      && value !== "closed"
    ) {
      return;
    }

    const status: OpportunityStatus =
      value;

    setOpportunities(
      (current) =>
        current.map(
          (opportunity) =>
            opportunity.opportunity_id
            === opportunityId
              ? {
                  ...opportunity,
                  current_status: status,
                }
              : opportunity
        )
    );
  }


  function updateOpportunityPriorityDraft(
    opportunityId: number,
    value: string
  ) {
    if (
      value !== "low"
      && value !== "medium"
      && value !== "high"
    ) {
      return;
    }

    const priority: OpportunityPriority =
      value;

    setOpportunities(
      (current) =>
        current.map(
          (opportunity) =>
            opportunity.opportunity_id
            === opportunityId
              ? {
                  ...opportunity,
                  priority: priority,
                }
              : opportunity
        )
    );
  }


  function updateOpportunityNotesDraft(
    opportunityId: number,
    notes: string
  ) {
    setOpportunities(
      (current) =>
        current.map(
          (opportunity) =>
            opportunity.opportunity_id
            === opportunityId
              ? {
                  ...opportunity,
                  notes: notes,
                }
              : opportunity
        )
    );
  }

  async function handleDeleteOpportunity(
    opportunity:
      OpportunitySummary
  ) {
    const confirmed =
      window.confirm(
        `Remove ${opportunity.raw_title} at ${opportunity.raw_company_name} from My Applications? This will also remove its application details and activity history.`
      );


    if (!confirmed) {
      return;
    }


    setDeletingOpportunityId(
      opportunity.opportunity_id
    );

    setError(
      null
    );


    const token =
      await getAccessToken();


    if (!token) {
      setError(
        "Your session has expired."
      );

      setDeletingOpportunityId(
        null
      );

      return;
    }


    const apiUrl =
      process.env
        .NEXT_PUBLIC_API_URL;


    try {
      const response =
        await fetch(
          `${apiUrl}/api/opportunities/${opportunity.opportunity_id}`,
          {
            method:
              "DELETE",

            headers: {
              Authorization:
                `Bearer ${token}`,
            },
          }
        );


      const data =
        await response.json();


      if (
        !response.ok
      ) {
        throw new Error(
          typeof data.detail
            === "string"
            ? data.detail
            : (
              "Failed to remove "
              + "application"
            )
        );
      }


      setEditingOpportunityId(
        null
      );

      setEditingApplicationOpportunityId(
        null
      );

      setHistoryOpportunityId(
        null
      );

      setAddingEventOpportunityId(
        null
      );


      await loadOpportunities(
        token
      );


      await loadOpportunityAnalytics(
        token
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : (
            "Failed to remove "
            + "application"
          )
      );

    } finally {
      setDeletingOpportunityId(
        null
      );
    }
  }


  async function saveOpportunityDetails(
    opportunity:
      OpportunitySummary
  ) {
    setUpdatingOpportunityId(
      opportunity
        .opportunity_id
    );

    setError(
      null
    );


    const token =
      await getAccessToken();


    if (!token) {
      setError(
        "Your session has expired."
      );

      setUpdatingOpportunityId(
        null
      );

      return;
    }


    const apiUrl =
      process.env
        .NEXT_PUBLIC_API_URL;


    try {
      const response =
        await fetch(
          `${apiUrl}/api/opportunities/${opportunity.opportunity_id}`,
          {
            method:
              "PATCH",

            headers: {
              "Content-Type":
                "application/json",

              Authorization:
                `Bearer ${token}`,
            },

            body:
              JSON.stringify({
                priority:
                  opportunity
                    .priority,

                notes:
                  opportunity
                    .notes,
              }),
          }
        );


      const data =
        await response.json();


      if (
        !response.ok
      ) {
        throw new Error(
          typeof data.detail
            === "string"

            ? data.detail

            : (
              "Failed to update "
              + "opportunity details"
            )
        );
      }


      await loadOpportunities(
        token
      );


      await loadOpportunityAnalytics(
        token
      );

      setEditingOpportunityId(
        null
      );


    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : (
            "Failed to update "
            + "opportunity details"
          )
      );

    } finally {
      setUpdatingOpportunityId(
        null
      );
    }
  }


  async function saveOpportunityStatus(
    opportunity:
      OpportunitySummary
  ) {
    setUpdatingOpportunityId(
      opportunity
        .opportunity_id
    );

    setError(
      null
    );


    const token =
      await getAccessToken();


    if (!token) {
      setError(
        "Your session has expired."
      );

      setUpdatingOpportunityId(
        null
      );

      return;
    }


    const apiUrl =
      process.env
        .NEXT_PUBLIC_API_URL;


    try {
      const response =
        await fetch(
          `${apiUrl}/api/opportunities/${opportunity.opportunity_id}/status`,
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
              JSON.stringify({
                status:
                  opportunity
                    .current_status,

                notes:
                  null,
              }),
          }
        );


      const data =
        await response.json();


      if (
        !response.ok
      ) {
        throw new Error(
          typeof data.detail
            === "string"

            ? data.detail

            : (
              "Failed to update "
              + "application stage"
            )
        );
      }


      await loadOpportunities(
        token
      );


      await loadOpportunityAnalytics(
        token
      );


      setEditingOpportunityId(
        null
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : (
            "Failed to update "
            + "application stage"
          )
      );

    } finally {
      setUpdatingOpportunityId(
        null
      );
    }
  }


  async function handleRecordApplication(
    event:
      FormEvent<
        HTMLFormElement
      >,

    opportunityId:
      number
  ) {
    event.preventDefault();


    const formData =
      new FormData(
        event.currentTarget
      );


    const currentResume =
      resumes[0]
      ?? null;


    const applicationUrl =
      String(
        formData.get(
          "application_url"
        )
        ?? ""
      ).trim();


    const applicationMethod =
      String(
        formData.get(
          "application_method"
        )
        ?? ""
      ).trim();


    const applicationNotes =
      String(
        formData.get(
          "application_notes"
        )
        ?? ""
      ).trim();


    setUpdatingOpportunityId(
      opportunityId
    );

    setError(
      null
    );


    const token =
      await getAccessToken();


    if (!token) {
      setError(
        "Your session has expired."
      );

      setUpdatingOpportunityId(
        null
      );

      return;
    }


    const apiUrl =
      process.env
        .NEXT_PUBLIC_API_URL;


    try {
      const response =
        await fetch(
          `${apiUrl}/api/opportunities/${opportunityId}/application`,
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
              JSON.stringify({
                resume_id:
                  currentResume
                    ?.resume_id
                  ?? null,

                application_url:
                  applicationUrl
                    || null,

                application_method:
                  applicationMethod
                    || null,

                referral_used:
                  formData.get(
                    "referral_used"
                  )
                  === "on",

                cover_letter_used:
                  formData.get(
                    "cover_letter_used"
                  )
                  === "on",

                notes:
                  applicationNotes
                    || null,
              }),
          }
        );


      const data =
        await response.json();


      if (
        !response.ok
      ) {
        throw new Error(
          typeof data.detail
            === "string"

            ? data.detail

            : (
              "Failed to record "
              + "application"
            )
        );
      }


      await loadOpportunities(
        token
      );


      await loadOpportunityAnalytics(
        token
      );


      setEditingApplicationOpportunityId(
        null
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : (
            "Failed to record "
            + "application"
          )
      );

    } finally {
      setUpdatingOpportunityId(
        null
      );
    }
  }


  function updateJobTypeFilter(
    value: string
  ) {
    if (
      value !== "all"
      && value !== "internship"
      && value !== "full_time"
      && value !== "part_time"
      && value !== "contract"
      && value !== "other"
    ) {
      return;
    }

    setJobTypeFilter(
      value
    );
  }


  function updateOpportunityStatusFilter(
    value: string
  ) {
    if (
      value !== "all"
      && value !== "discovered"
      && value !== "saved"
      && value !== "to_apply"
      && value !== "applied"
      && value !== "oa"
      && value !== "interview"
      && value !== "offer"
      && value !== "rejected"
      && value !== "withdrawn"
      && value !== "closed"
    ) {
      return;
    }

    setOpportunityStatusFilter(
      value
    );
  }


  function updateOpportunityPriorityFilter(
    value: string
  ) {
    if (
      value !== "all"
      && value !== "low"
      && value !== "medium"
      && value !== "high"
    ) {
      return;
    }

    setOpportunityPriorityFilter(
      value
    );
  }


  function updateOpportunitySort(
    value: string
  ) {
    if (
      value !== "attention"
      && value !== "priority"
      && value !== "deadline"
      && value !== "stage"
      && value !== "company"
      && value !== "title"
      && value !== "recent_application"
    ) {
      return;
    }

    setOpportunitySort(
      value
    );
  }


  const stageOrder:
    Record<
      OpportunityStatus,
      number
    > = {
      discovered: 0,
      saved: 1,
      to_apply: 2,
      applied: 3,
      oa: 4,
      interview: 5,
      offer: 6,
      rejected: 7,
      withdrawn: 8,
      closed: 9,
    };


  const priorityOrder:
    Record<
      OpportunityPriority,
      number
    > = {
      high: 0,
      medium: 1,
      low: 2,
    };


  const normalizedOpportunitySearch =
    opportunitySearch
      .trim()
      .toLowerCase();


  const visibleOpportunities =
    opportunities
      .filter(
        (
          opportunity
        ) => {
          if (
            opportunityStatusFilter
            !== "all"
            && opportunity.current_status
            !== opportunityStatusFilter
          ) {
            return false;
          }


          if (
            opportunityPriorityFilter
            !== "all"
            && opportunity.priority
            !== opportunityPriorityFilter
          ) {
            return false;
          }


          if (
            !normalizedOpportunitySearch
          ) {
            return true;
          }


          const searchableText =
            [
              opportunity.raw_title,
              opportunity.raw_company_name,
              opportunity.location_raw,
              opportunity.search_query,
              opportunity.notes,
            ]
              .filter(
                (
                  value
                ) => Boolean(
                  value
                )
              )
              .join(" ")
              .toLowerCase();


          return searchableText.includes(
            normalizedOpportunitySearch
          );
        }
      )
      .sort(
        (
          left,
          right
        ) => {
          if (
            opportunitySort
            === "attention"
          ) {
            const leftHasEvent =
              Boolean(
                left.next_event_at
              );

            const rightHasEvent =
              Boolean(
                right.next_event_at
              );


            if (
              leftHasEvent
              !== rightHasEvent
            ) {
              return leftHasEvent
                ? -1
                : 1;
            }


            if (
              left.next_event_at
              && right.next_event_at
            ) {
              const deadlineDifference =
                new Date(
                  left.next_event_at
                ).getTime()
                - new Date(
                  right.next_event_at
                ).getTime();


              if (
                deadlineDifference
                !== 0
              ) {
                return deadlineDifference;
              }
            }


            const priorityDifference =
              priorityOrder[
                left.priority
              ]
              - priorityOrder[
                right.priority
              ];


            if (
              priorityDifference
              !== 0
            ) {
              return priorityDifference;
            }


            return stageOrder[
              left.current_status
            ]
            - stageOrder[
              right.current_status
            ];
          }


          if (
            opportunitySort
            === "deadline"
          ) {
            if (
              left.next_event_at
              && right.next_event_at
            ) {
              return (
                new Date(
                  left.next_event_at
                ).getTime()
                - new Date(
                  right.next_event_at
                ).getTime()
              );
            }


            if (
              left.next_event_at
            ) {
              return -1;
            }


            if (
              right.next_event_at
            ) {
              return 1;
            }


            return priorityOrder[
              left.priority
            ]
            - priorityOrder[
              right.priority
            ];
          }


          if (
            opportunitySort
            === "priority"
          ) {
            const priorityDifference =
              priorityOrder[
                left.priority
              ]
              - priorityOrder[
                right.priority
              ];

            if (
              priorityDifference
              !== 0
            ) {
              return priorityDifference;
            }

            return stageOrder[
              left.current_status
            ]
            - stageOrder[
              right.current_status
            ];
          }


          if (
            opportunitySort
            === "stage"
          ) {
            return stageOrder[
              left.current_status
            ]
            - stageOrder[
              right.current_status
            ];
          }


          if (
            opportunitySort
            === "company"
          ) {
            return left
              .raw_company_name
              .localeCompare(
                right.raw_company_name
              );
          }


          if (
            opportunitySort
            === "title"
          ) {
            return left
              .raw_title
              .localeCompare(
                right.raw_title
              );
          }


          const leftSubmittedAt =
            left.submitted_at
              ? new Date(
                  left.submitted_at
                ).getTime()
              : 0;

          const rightSubmittedAt =
            right.submitted_at
              ? new Date(
                  right.submitted_at
                ).getTime()
              : 0;

          return (
            rightSubmittedAt
            - leftSubmittedAt
          );
        }
      );


  const hasOpportunityFilters =
    Boolean(
      normalizedOpportunitySearch
    )
    || opportunityStatusFilter
      !== "all"
    || opportunityPriorityFilter
      !== "all";


  const availableJobStartMonths:
    string[] =
      Array.from(
        new Set<string>(
          jobs
            .map(
              extractExplicitJobStartMonth
            )
            .filter(
              (
                value
              ): value is string =>
                value !== null
            )
        )
      ).sort();


  const visibleJobs =
    jobs.filter(
      (
        job
      ) => {
        if (
          jobTypeFilter
          !== "all"
          && classifyJobType(
            job
          )
          !== jobTypeFilter
        ) {
          return false;
        }


        if (
          jobStartMonthFilter
          === "unknown"
        ) {
          return (
            extractExplicitJobStartMonth(
              job
            )
            === null
          );
        }


        if (
          jobStartMonthFilter
          !== "all"
          && extractExplicitJobStartMonth(
            job
          )
          !== jobStartMonthFilter
        ) {
          return false;
        }


        return true;
      }
    ).sort(
      (
        left,
        right
      ) => {
        // Search relevance remains the primary ordering signal.
        // Resume match is informational only: CareerLens is designed
        // to help users tailor their resume to relevant roles rather
        // than hide relevant roles because of current resume gaps.
        const leftSearch =
          left.search_relevance;

        const rightSearch =
          right.search_relevance;


        if (
          leftSearch !== null
          || rightSearch !== null
        ) {
          if (
            leftSearch === null
          ) {
            return 1;
          }

          if (
            rightSearch === null
          ) {
            return -1;
          }

          if (
            rightSearch
            !== leftSearch
          ) {
            return (
              rightSearch
              - leftSearch
            );
          }
        }


        // Preserve the provider's original order when search
        // relevance ties or is unavailable.
        return (
          (
            left.provider_rank
            ?? Number.MAX_SAFE_INTEGER
          )
          -
          (
            right.provider_rank
            ?? Number.MAX_SAFE_INTEGER
          )
        );
      }
    );


  const hasJobFilters =
    jobTypeFilter
    !== "all"
    || jobStartMonthFilter
      !== "all";


  if (
    loading
  ) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center px-4">
        <div className="flex max-w-md flex-col items-center rounded-2xl border border-slate-200 bg-white px-8 py-10 text-center shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <LoadingSpinner
            className="h-9 w-9 text-[#0A66C2]"
            label="Loading your CareerCompass workspace"
          />

          <p className="mt-4 font-semibold text-slate-900 dark:text-white">
            Loading your workspace...
          </p>

          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Getting your profile, applications and latest results ready. This can take a little longer after a period of inactivity.
          </p>

          <p className="mt-3 rounded-full bg-blue-50 px-3 py-1.5 text-xs font-semibold text-[#0A66C2] dark:bg-blue-950/40 dark:text-blue-200">
            Estimated time: 10–20 seconds
          </p>
        </div>
      </div>
    );
  }


  return (
    <div className="w-full space-y-6 overflow-x-hidden font-sans text-slate-900">
{error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}


      <CareerCompassHeader
        activeView={
          activeView
        }
        onViewChange={
          setActiveView
        }
        jobCount={
          jobs.length
        }
        applicationCount={
          opportunities.length
        }
        resumeCount={
          resumes.length
        }
        query={
          query
        }
        location={
          location
        }
        searching={
          searching
        }
        remainingSearches={
          quota?.remaining
          ?? null
        }
        searchLimit={
          quota?.limit
          ?? 2
        }
        onQueryChange={
          setQuery
        }
        onLocationChange={
          setLocation
        }
        onSearch={
          handleSearch
        }
        onOpportunitySaved={
          handleManualOpportunitySaved
        }
        userEmail={
          userEmail
        }
      />


      <div
        id="careercompass-content"
        className="mx-auto box-border w-full max-w-6xl scroll-mt-4 px-[1cm]"
      >


      {
        activeView
        === "applications"
        && (
          <div className="space-y-6 pt-6">

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-blue-200 hover:shadow-md">

        <div className="flex flex-wrap items-start justify-between gap-3">

          <div>
            <h2 className="text-xl font-semibold">
              My Applications
            </h2>

            <p className="mt-1 text-sm text-gray-600">
              Keep every role you care about in one place and update its progress as you move through the hiring process.
            </p>
          </div>


          <span className="rounded bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700">
            {opportunities.length} applications
          </span>

        </div>


        {opportunities.length > 0 && (

          <div className="mt-5 rounded-xl border border-blue-100 bg-blue-50/50 p-4">

            <div className="grid gap-3 lg:grid-cols-[2fr_1fr_1fr_1fr_auto]">

              <input
                value={
                  opportunitySearch
                }

                onChange={(event) =>
                  setOpportunitySearch(
                    event.target.value
                  )
                }

                placeholder="Search role, company, location or notes"

                className="rounded border bg-white px-3 py-2 text-sm"
              />


              <select
                value={
                  opportunityStatusFilter
                }

                onChange={(event) =>
                  updateOpportunityStatusFilter(
                    event.target.value
                  )
                }

                className="rounded border bg-white px-3 py-2 text-sm"
              >
                <option value="all">
                  All stages
                </option>

                <option value="discovered">
                  Discovered
                </option>

                <option value="saved">
                  Saved
                </option>

                <option value="to_apply">
                  To Apply
                </option>

                <option value="applied">
                  Applied
                </option>

                <option value="oa">
                  OA
                </option>

                <option value="interview">
                  Interview
                </option>

                <option value="offer">
                  Offer
                </option>

                <option value="rejected">
                  Rejected
                </option>

                <option value="withdrawn">
                  Withdrawn
                </option>

                <option value="closed">
                  Closed
                </option>
              </select>


              <select
                value={
                  opportunityPriorityFilter
                }

                onChange={(event) =>
                  updateOpportunityPriorityFilter(
                    event.target.value
                  )
                }

                className="rounded border bg-white px-3 py-2 text-sm"
              >
                <option value="all">
                  All priorities
                </option>

                <option value="high">
                  High priority
                </option>

                <option value="medium">
                  Medium priority
                </option>

                <option value="low">
                  Low priority
                </option>
              </select>


              <select
                value={
                  opportunitySort
                }

                onChange={(event) =>
                  updateOpportunitySort(
                    event.target.value
                  )
                }

                className="rounded border bg-white px-3 py-2 text-sm"
              >
                <option value="attention">
                  Sort: Priority & deadlines
                </option>

                <option value="deadline">
                  Sort: Upcoming deadline
                </option>

                <option value="priority">
                  Sort: Priority
                </option>

                <option value="stage">
                  Sort: Stage
                </option>

                <option value="recent_application">
                  Sort: Recent application
                </option>

                <option value="company">
                  Sort: Company
                </option>

                <option value="title">
                  Sort: Job title
                </option>
              </select>


              <button
                type="button"

                onClick={() => {
                  setOpportunitySearch(
                    ""
                  );

                  setOpportunityStatusFilter(
                    "all"
                  );

                  setOpportunityPriorityFilter(
                    "all"
                  );
                }}

                disabled={
                  !hasOpportunityFilters
                }

                className="rounded border bg-white px-4 py-2 text-sm font-medium hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Clear
              </button>

            </div>


            <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500">

              <span>
                Showing {
                  visibleOpportunities.length
                } of {
                  opportunities.length
                } tracked opportunities
              </span>


              {
                hasOpportunityFilters
                && (
                  <span>
                    Filters are active
                  </span>
                )
              }

            </div>

          </div>

        )}


        {opportunities.length === 0 && (

          <div className="mt-5 rounded-lg border border-dashed p-4 text-sm text-gray-600">
            No applications saved yet.
            Use the Save to My Applications button on a job result to add it here.
          </div>

        )}


        <ApplicationPipeline
          opportunities={
            visibleOpportunities
          }
        />


        {opportunities.length > 0
        && visibleOpportunities.length > 0
        && (

          <div className="mt-8 border-t border-slate-200 pt-6">

            <div>
              <h3 className="text-lg font-semibold text-slate-900">
                Manage Applications
              </h3>

              <p className="mt-1 text-sm text-slate-600">
                Update stages, record application details, add milestones and review activity history.
              </p>
            </div>


            <div className="mt-4 space-y-4">

            {visibleOpportunities.map((opportunity) => (

              <div
                key={opportunity.opportunity_id}
                id={`application-${opportunity.opportunity_id}`}
                className="scroll-mt-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
              >

                <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">

                  <div>

                    <p className="font-semibold text-gray-900">
                      {opportunity.raw_title}
                    </p>


                    <p className="mt-1 text-sm font-medium text-gray-700">
                      {opportunity.raw_company_name}
                    </p>


                    {opportunity.location_raw && (

                      <p className="mt-1 text-sm text-gray-500">
                        {opportunity.location_raw}
                      </p>

                    )}


                    {opportunity.search_query && (

                      <p className="mt-2 text-xs text-gray-500">
                        From search:{" "}

                        <strong>
                          {opportunity.search_query}
                        </strong>
                      </p>

                    )}


                    {
                      opportunity.source
                      === "manual_url"
                      && (
                        <p className="mt-2 text-xs font-medium text-[#0A66C2]">
                          Imported job listing
                        </p>
                      )
                    }

                  </div>


                  <div className="flex flex-wrap gap-2">

                    <span
                      className={
                        "rounded-full px-2.5 py-1 text-xs font-semibold "
                        + getOpportunityStatusClass(
                          opportunity.current_status
                        )
                      }
                    >
                      {formatText(
                        opportunity.current_status
                      )}
                    </span>


                    <span
                      className={
                        "rounded px-2.5 py-1 text-xs font-medium "
                        + getOpportunityPriorityClass(
                          opportunity.priority
                        )
                      }
                    >
                      {formatText(
                        opportunity.priority
                      )}{" "}
                      priority
                    </span>

                  </div>

                </div>


                {opportunity.notes && (

                  <div className="mt-3 rounded bg-gray-50 p-3 text-sm text-gray-600">
                    {opportunity.notes}
                  </div>

                )}


                {opportunity.next_event_at && (

                  <div className="mt-3 rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">

                    <p className="font-medium">
                      Next {
                        opportunity.next_event_type
                          ? formatText(
                              opportunity.next_event_type
                            )
                          : "event"
                      }
                      {": "}
                      {
                        formatDateTime(
                          opportunity.next_event_at
                        )
                      }
                    </p>


                    {opportunity.next_event_notes && (
                      <p className="mt-1 text-xs">
                        {
                          opportunity.next_event_notes
                        }
                      </p>
                    )}

                  </div>

                )}


                <div className="mt-4 flex flex-wrap items-start gap-2">

                  <div className="w-full md:w-auto">

                    <button
                      type="button"

                      onClick={() => {
                        setEditingApplicationOpportunityId(
                          null
                        );

                        setHistoryOpportunityId(
                          null
                        );

                        setAddingEventOpportunityId(
                          null
                        );

                        setEditingOpportunityId(
                          (
                            current
                          ) =>
                            current
                            === opportunity.opportunity_id
                              ? null
                              : opportunity.opportunity_id
                        );
                      }}

                      className="rounded bg-[#0A66C2] px-4 py-2 text-sm font-medium text-white hover:bg-[#004182]"
                    >
                      {
                        editingOpportunityId
                        === opportunity.opportunity_id
                          ? "Close update"
                          : "Update"
                      }
                    </button>


                    {
                      editingOpportunityId
                      === opportunity.opportunity_id
                      && (

                        <div className="mt-4 w-full rounded-lg border bg-gray-50 p-4 md:min-w-[650px]">

                          <div className="grid gap-4 md:grid-cols-2">

                            <div>

                              <label className="text-xs font-medium uppercase tracking-wide text-gray-500">
                                Application stage
                              </label>


                              <select
                                value={opportunity.current_status}

                                onChange={(event) =>
                                  updateOpportunityStatusDraft(
                                    opportunity.opportunity_id,
                                    event.target.value
                                  )
                                }

                                className="mt-2 w-full rounded border bg-white px-3 py-2 text-sm"
                              >

                                <option value="discovered">
                                  Discovered
                                </option>

                                <option value="saved">
                                  Saved
                                </option>

                                <option value="to_apply">
                                  To Apply
                                </option>

                                <option value="applied">
                                  Applied
                                </option>

                                <option value="oa">
                                  OA
                                </option>

                                <option value="interview">
                                  Interview
                                </option>

                                <option value="offer">
                                  Offer
                                </option>

                                <option value="rejected">
                                  Rejected
                                </option>

                                <option value="withdrawn">
                                  Withdrawn
                                </option>

                                <option value="closed">
                                  Closed
                                </option>

                              </select>

                            </div>


                            <div>

                              <label className="text-xs font-medium uppercase tracking-wide text-gray-500">
                                Priority
                              </label>


                              <select
                                value={opportunity.priority}

                                onChange={(event) =>
                                  updateOpportunityPriorityDraft(
                                    opportunity.opportunity_id,
                                    event.target.value
                                  )
                                }

                                className="mt-2 w-full rounded border bg-white px-3 py-2 text-sm"
                              >

                                <option value="low">
                                  Low
                                </option>

                                <option value="medium">
                                  Medium
                                </option>

                                <option value="high">
                                  High
                                </option>

                              </select>

                            </div>

                          </div>


                          <div className="mt-4">

                            <label className="text-xs font-medium uppercase tracking-wide text-gray-500">
                              Notes
                            </label>


                            <textarea
                              value={
                                opportunity.notes
                                ?? ""
                              }

                              onChange={(event) =>
                                updateOpportunityNotesDraft(
                                  opportunity.opportunity_id,
                                  event.target.value
                                )
                              }

                              rows={3}

                              placeholder="Add notes about this opportunity..."

                              className="mt-2 w-full rounded border bg-white px-3 py-2 text-sm"
                            />

                          </div>


                          <div className="mt-4 flex flex-wrap gap-2">

                            <button
                              type="button"

                              onClick={() =>
                                saveOpportunityStatus(
                                  opportunity
                                )
                              }

                              disabled={
                                updatingOpportunityId
                                === opportunity.opportunity_id
                              }

                              className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#0A66C2] px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-[#004182] disabled:cursor-not-allowed disabled:opacity-50"
                            >

                              {
                                updatingOpportunityId
                                === opportunity.opportunity_id
                                && (
                                  <LoadingSpinner
                                    label="Updating application stage"
                                  />
                                )
                              }

                              {
                                updatingOpportunityId
                                === opportunity.opportunity_id
                                  ? "Saving..."
                                  : "Update stage"
                              }

                            </button>


                            <button
                              type="button"

                              onClick={() =>
                                saveOpportunityDetails(
                                  opportunity
                                )
                              }

                              disabled={
                                updatingOpportunityId
                                === opportunity.opportunity_id
                              }

                              className="inline-flex items-center justify-center gap-2 rounded border bg-white px-4 py-2 text-sm font-medium hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                            >

                              {
                                updatingOpportunityId
                                === opportunity.opportunity_id
                                && (
                                  <LoadingSpinner
                                    label="Saving opportunity details"
                                  />
                                )
                              }

                              {
                                updatingOpportunityId
                                === opportunity.opportunity_id
                                  ? "Saving..."
                                  : "Save priority & notes"
                              }

                            </button>

                          </div>

                        </div>

                      )
                    }

                  </div>


                  <div className="w-full md:w-auto">

                    <button
                      type="button"

                      onClick={() => {
                        setEditingOpportunityId(
                          null
                        );

                        setHistoryOpportunityId(
                          null
                        );

                        setAddingEventOpportunityId(
                          null
                        );

                        setEditingApplicationOpportunityId(
                          (
                            current
                          ) =>
                            current
                            === opportunity.opportunity_id
                              ? null
                              : opportunity.opportunity_id
                        );
                      }}

                      className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                    >
                      {
                        editingApplicationOpportunityId
                        === opportunity.opportunity_id
                          ? "Close application"
                          : opportunity.application_id
                            ? "Edit Application"
                            : "Log Application"
                      }
                    </button>


                    {
                      editingApplicationOpportunityId
                      === opportunity.opportunity_id
                      && (

                        <form
                          onSubmit={(event) =>
                            handleRecordApplication(
                              event,
                              opportunity.opportunity_id
                            )
                          }

                          className="mt-4 w-full rounded-lg border bg-gray-50 p-4 md:min-w-[650px]"
                        >

                          {opportunity.application_id && (

                            <div className="mb-4 rounded border border-green-200 bg-green-50 p-3 text-sm text-green-800">

                              <p className="font-medium">
                                Application recorded
                              </p>

                              {opportunity.submitted_at && (
                                <p className="mt-1 text-xs">
                                  Recorded:{" "}
                                  {formatDateTime(
                                    opportunity.submitted_at
                                  )}
                                </p>
                              )}

                            </div>

                          )}


                          <div className="grid gap-4 md:grid-cols-2">

                            <div>

                              <label className="text-xs font-medium uppercase tracking-wide text-gray-500">
                                Current resume
                              </label>


                              <div className="mt-2 rounded border bg-slate-50 px-3 py-2 text-sm text-slate-700">
                                {
                                  resumes[0]
                                    ?.original_filename
                                  ?? "No resume uploaded"
                                }
                              </div>


                              <p className="mt-1 text-xs text-gray-500">
                                CareerCompass uses your single current resume for new application records and comparisons.
                              </p>

                            </div>


                            <div>

                              <label className="text-xs font-medium uppercase tracking-wide text-gray-500">
                                Application method
                              </label>


                              <input
                                name="application_method"
                                type="text"

                                defaultValue={
                                  opportunity.application_method
                                  ?? ""
                                }

                                placeholder="e.g. company website, LinkedIn, referral"

                                className="mt-2 w-full rounded border bg-white px-3 py-2 text-sm"
                              />

                            </div>

                          </div>


                          <div className="mt-4">

                            <label className="text-xs font-medium uppercase tracking-wide text-gray-500">
                              Application URL
                            </label>


                            <input
                              name="application_url"
                              type="url"

                              defaultValue={
                                opportunity.application_url
                                ?? ""
                              }

                              placeholder="https://..."

                              className="mt-2 w-full rounded border bg-white px-3 py-2 text-sm"
                            />

                          </div>


                          <div className="mt-4 flex flex-wrap gap-5">

                            <label className="flex items-center gap-2 text-sm text-gray-700">
                              <input
                                name="referral_used"
                                type="checkbox"
                                defaultChecked={
                                  Boolean(
                                    opportunity.referral_used
                                  )
                                }
                              />

                              Referral used
                            </label>


                            <label className="flex items-center gap-2 text-sm text-gray-700">
                              <input
                                name="cover_letter_used"
                                type="checkbox"
                                defaultChecked={
                                  Boolean(
                                    opportunity.cover_letter_used
                                  )
                                }
                              />

                              Cover letter used
                            </label>

                          </div>


                          <div className="mt-4">

                            <label className="text-xs font-medium uppercase tracking-wide text-gray-500">
                              Application notes
                            </label>


                            <textarea
                              name="application_notes"

                              defaultValue={
                                opportunity.application_notes
                                ?? ""
                              }

                              rows={3}

                              placeholder="Add notes about the submitted application..."

                              className="mt-2 w-full rounded border bg-white px-3 py-2 text-sm"
                            />

                          </div>


                          <p className="mt-3 text-xs text-gray-500">
                            Recording an application moves Discovered, Saved or To Apply to Applied. Later stages are not moved backwards.
                          </p>


                          <button
                            type="submit"

                            disabled={
                              updatingOpportunityId
                              === opportunity.opportunity_id
                            }

                            className="mt-4 inline-flex items-center justify-center gap-2 rounded bg-[#0A66C2] px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            {
                              updatingOpportunityId
                              === opportunity.opportunity_id
                              && (
                                <LoadingSpinner
                                  label="Saving application details"
                                />
                              )
                            }

                            {
                              updatingOpportunityId
                              === opportunity.opportunity_id
                                ? "Saving..."
                                : opportunity.application_id
                                  ? "Save application details"
                                  : "Log Application"
                            }
                          </button>

                        </form>

                      )
                    }

                  </div>


                  <div className="w-full md:w-auto">

                    <button
                      type="button"

                      onClick={() =>
                        toggleAddOpportunityEvent(
                          opportunity.opportunity_id
                        )
                      }

                      className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                    >
                      {
                        addingEventOpportunityId
                        === opportunity.opportunity_id
                          ? "Close update"
                          : "Add Update"
                      }
                    </button>


                    {
                      addingEventOpportunityId
                      === opportunity.opportunity_id
                      && (

                        <form
                          onSubmit={(event) =>
                            handleAddOpportunityEvent(
                              event,
                              opportunity.opportunity_id
                            )
                          }

                          className="mt-4 w-full rounded-lg border bg-gray-50 p-4 md:min-w-[650px]"
                        >

                          <div className="grid gap-4 md:grid-cols-2">

                            <div>

                              <label className="text-xs font-medium uppercase tracking-wide text-gray-500">
                                Event type
                              </label>


                              <select
                                value={
                                  newEventType
                                }

                                onChange={(event) =>
                                  updateNewEventType(
                                    event.target.value
                                  )
                                }

                                className="mt-2 w-full rounded border bg-white px-3 py-2 text-sm"
                              >
                                <option value="note">
                                  Note
                                </option>

                                <option value="deadline">
                                  Deadline
                                </option>

                                <option value="follow_up">
                                  Follow up
                                </option>

                                <option value="oa">
                                  OA
                                </option>

                                <option value="interview">
                                  Interview
                                </option>

                                <option value="offer">
                                  Offer
                                </option>

                                <option value="rejection">
                                  Rejection
                                </option>

                                <option value="withdrawal">
                                  Withdrawal
                                </option>

                                <option value="other">
                                  Other
                                </option>
                              </select>

                            </div>


                            <div>

                              <label className="text-xs font-medium uppercase tracking-wide text-gray-500">
                                Date and time
                              </label>


                              <input
                                type="datetime-local"

                                value={
                                  newEventAt
                                }

                                onChange={(event) =>
                                  setNewEventAt(
                                    event.target.value
                                  )
                                }

                                required

                                className="mt-2 w-full rounded border bg-white px-3 py-2 text-sm"
                              />

                            </div>

                          </div>


                          <div className="mt-4">

                            <label className="text-xs font-medium uppercase tracking-wide text-gray-500">
                              Notes
                            </label>


                            <textarea
                              value={
                                newEventNotes
                              }

                              onChange={(event) =>
                                setNewEventNotes(
                                  event.target.value
                                )
                              }

                              rows={3}

                              placeholder="e.g. OA due Friday, interview with hiring manager, send follow-up email..."

                              className="mt-2 w-full rounded border bg-white px-3 py-2 text-sm"
                            />

                          </div>


                          <p className="mt-3 text-xs text-gray-500">
                            Events add timeline context. Use Update if you also want to change the opportunity&apos;s current application stage.
                          </p>


                          <button
                            type="submit"

                            disabled={
                              savingEventOpportunityId
                              === opportunity.opportunity_id
                            }

                            className="mt-4 inline-flex items-center justify-center gap-2 rounded bg-[#0A66C2] px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            {
                              savingEventOpportunityId
                              === opportunity.opportunity_id
                              && (
                                <LoadingSpinner
                                  label="Saving activity event"
                                />
                              )
                            }

                            {
                              savingEventOpportunityId
                              === opportunity.opportunity_id
                                ? "Saving..."
                                : "Save event"
                            }
                          </button>

                        </form>

                      )
                    }

                  </div>


                  <button
                    type="button"

                    onClick={() =>
                      toggleOpportunityHistory(
                        opportunity.opportunity_id
                      )
                    }

                    disabled={
                      loadingHistoryOpportunityId
                      === opportunity.opportunity_id
                    }

                    className="inline-flex items-center justify-center gap-2 rounded border px-4 py-2 text-sm font-medium hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {
                      loadingHistoryOpportunityId
                      === opportunity.opportunity_id
                      && (
                        <LoadingSpinner
                          label="Loading opportunity activity"
                        />
                      )
                    }

                    {
                      loadingHistoryOpportunityId
                      === opportunity.opportunity_id
                        ? "Loading..."
                        : historyOpportunityId
                          === opportunity.opportunity_id
                          ? "Close activity"
                          : "Activity"
                    }
                  </button>


                  <button
                    type="button"

                    onClick={() =>
                      handleDeleteOpportunity(
                        opportunity
                      )
                    }

                    disabled={
                      deletingOpportunityId
                      === opportunity.opportunity_id
                    }

                    className="inline-flex items-center justify-center gap-2 rounded border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-medium text-rose-700 hover:bg-rose-100 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {
                      deletingOpportunityId
                      === opportunity.opportunity_id
                      && (
                        <LoadingSpinner
                          label="Removing application"
                        />
                      )
                    }

                    {
                      deletingOpportunityId
                      === opportunity.opportunity_id
                        ? "Removing..."
                        : "Remove"
                    }
                  </button>


                  <a
                    href={opportunity.job_url}

                    target="_blank"

                    rel="noopener noreferrer"

                    className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  >
                    View Posting
                  </a>


                </div>


                <ApplicationResumeComparison
                  opportunityId={
                    opportunity.opportunity_id
                  }
                />


                {
                  historyOpportunityId
                  === opportunity.opportunity_id
                  && (

                    <div className="mt-4 rounded-lg border bg-gray-50 p-4">

                      <div className="flex flex-wrap items-start justify-between gap-3">

                        <div>

                          <p className="font-semibold text-gray-900">
                            Opportunity history
                          </p>


                          <p className="mt-1 text-xs text-gray-500">
                            Recorded changes and milestones for this opportunity.
                          </p>

                        </div>


                        <span className="rounded bg-white px-2.5 py-1 text-xs text-gray-500">
                          {
                            opportunityEvents[
                              opportunity.opportunity_id
                            ]
                              ?.length
                            ?? 0
                          }{" "}
                          events
                        </span>

                      </div>


                      {
                        loadingHistoryOpportunityId
                        === opportunity.opportunity_id
                        ? (

                          <div className="mt-4 flex items-center gap-2 text-sm text-gray-500">
                            <LoadingSpinner
                              label="Loading opportunity history"
                            />

                            <span>
                              Loading history...
                            </span>
                          </div>

                        )
                        : (
                          opportunityEvents[
                            opportunity.opportunity_id
                          ]
                          ?? []
                        ).length
                        === 0
                        ? (

                          <p className="mt-4 text-sm text-gray-500">
                            No history has been recorded yet.
                          </p>

                        )
                        : (

                          <div className="mt-4 space-y-3">

                            {
                              (
                                opportunityEvents[
                                  opportunity.opportunity_id
                                ]
                                ?? []
                              )
                                .slice()
                                .reverse()
                                .map(
                                  (
                                    event
                                  ) => (

                                    <div
                                      key={
                                        event.event_id
                                      }

                                      className="rounded border bg-white p-3"
                                    >

                                      <div className="flex flex-wrap items-start justify-between gap-2">

                                        <div>

                                          <p className="text-sm font-medium text-gray-900">
                                            {
                                              formatText(
                                                event.event_type
                                              )
                                            }
                                          </p>


                                          {
                                            event.from_status
                                            && event.to_status
                                            && (

                                              <p className="mt-1 text-sm text-gray-700">
                                                {
                                                  formatText(
                                                    event.from_status
                                                  )
                                                }
                                                {" → "}
                                                {
                                                  formatText(
                                                    event.to_status
                                                  )
                                                }
                                              </p>

                                            )
                                          }


                                          {
                                            !event.from_status
                                            && event.to_status
                                            && (

                                              <p className="mt-1 text-sm text-gray-700">
                                                Stage:{" "}
                                                {
                                                  formatText(
                                                    event.to_status
                                                  )
                                                }
                                              </p>

                                            )
                                          }

                                        </div>


                                        <span className="text-xs text-gray-500">
                                          {
                                            formatDateTime(
                                              event.event_at
                                            )
                                          }
                                        </span>

                                      </div>


                                      {
                                        event.notes
                                        && (

                                          <p className="mt-2 text-sm text-gray-600">
                                            {
                                              event.notes
                                            }
                                          </p>

                                        )
                                      }


                                      {
                                        event.event_source
                                        && (

                                          <p className="mt-2 text-xs text-gray-400">
                                            Source:{" "}
                                            {
                                              formatText(
                                                event.event_source
                                              )
                                            }
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
                }

              </div>

            ))}

            </div>

          </div>

        )}


        {opportunities.length > 0
        && visibleOpportunities.length === 0
        && (

          <div className="mt-5 rounded-lg border border-dashed p-4 text-sm text-gray-600">
            No applications match the current filters.
          </div>

        )}

      </section>





          </div>
        )
      }


      {
        activeView
        === "insights"
        && (
          <div className="pt-6">
      <SkillGapPanel
        refreshKey={
          [
            jobs
              .map(
                (job) =>
                  job.job_id
              )
              .join(","),

            resumes
              .map(
                (resume) =>
                  resume.resume_id
              )
              .join(","),
          ].join("|")
        }
      />
          </div>
        )
      }


      {
        activeView
        === "profile"
        && (
          <div className="space-y-6 pt-6">

      <section
        id="careercompass-resume-upload"
        className="scroll-mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
      >

        <div className="flex flex-wrap items-start justify-between gap-3">

          <div>

            <h2 className="text-xl font-semibold">
              Current Resume
            </h2>


            <p className="mt-1 max-w-2xl text-sm text-gray-600">
              CareerCompass keeps one resume for your profile. Every job comparison uses this resume.
            </p>

          </div>


          {
            resumes[0]
            && (
              <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                Active resume
              </span>
            )
          }

        </div>


        {
          resumes[0]
          ? (
            <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50/60 p-4">

              <p className="font-semibold text-slate-900">
                {
                  resumes[0]
                    .original_filename
                }
              </p>


              <p className="mt-1 text-xs text-gray-500">
                {
                  resumes[0]
                    .file_type
                    .toUpperCase()
                }

                {" · "}

                {
                  resumes[0]
                    .claim_count
                }{" "}
                extracted profile points

                {" · "}

                {
                  resumes[0]
                    .evidence_count
                }{" "}
                supporting details
              </p>


              <p className="mt-3 text-xs leading-5 text-slate-500">
                Uploading another resume will replace this one. Previous resume-derived profile evidence will no longer be used in job comparisons.
              </p>

            </div>
          )
          : (
            <div className="mt-5 rounded-xl border border-dashed border-slate-300 bg-slate-50/60 p-4 text-sm text-slate-600">
              No resume uploaded yet. Add one to enable resume comparisons.
            </div>
          )
        }


        <form
          onSubmit={
            handleResumeUpload
          }
          className="mt-5 flex flex-col gap-3 md:flex-row md:items-center"
        >

          <input
            id="careercompass-resume-file"
            type="file"

            accept={
              ".pdf,.docx,.txt"
            }

            onChange={
              (event) =>
                setSelectedFile(
                  event.target
                    .files?.[0]
                  ?? null
                )
            }

            className="sr-only"
          />


          <label
            htmlFor="careercompass-resume-file"
            className="inline-flex cursor-pointer items-center justify-center rounded-lg border border-blue-200 bg-blue-50 px-5 py-2.5 text-sm font-bold text-[#0A66C2] shadow-sm transition hover:bg-blue-100"
          >
            {
              resumes[0]
                ? "Choose Replacement"
                : "Choose Resume"
            }
          </label>


          <div className="min-w-0 flex-1">

            <p className="truncate text-sm text-slate-600">
              {
                selectedFile
                  ? selectedFile.name
                  : resumes[0]
                    ? "Choose a new file to replace your current resume"
                    : "No file selected"
              }
            </p>

          </div>


          <button
            type="submit"

            disabled={
              uploading
              || !selectedFile
            }

            className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#0A66C2] px-5 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-[#004182] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {
              uploading
              && (
                <LoadingSpinner
                  label={
                    resumes[0]
                      ? "Replacing resume"
                      : "Processing resume"
                  }
                />
              )
            }

            {
              uploading
                ? (
                  resumes[0]
                    ? "Replacing..."
                    : "Processing..."
                )
                : (
                  resumes[0]
                    ? "Replace Resume"
                    : "Upload Resume"
                )
            }
          </button>

        </form>


        {
          resumes[0]
          && selectedFile
          && (
            <p className="mt-3 text-xs font-medium text-amber-700">
              Replacing your resume will refresh CareerCompass profile matching using the new file.
            </p>
          )
        }


        {resumeMessage && (
          <div className="mt-4 rounded border border-green-200 bg-green-50 p-3 text-sm text-green-800">
            {
              resumeMessage
            }
          </div>
        )}

      </section>


      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">

        <div className="flex items-start justify-between gap-4">

          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Job search allowance
            </p>

            <h2 className="mt-1 text-xl font-semibold text-slate-900">
              Provider Searches
            </h2>
          </div>


          <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-[#0A66C2]">
            {
              quota
                ?.remaining
              ?? 0
            } remaining
          </span>

        </div>


        <div className="mt-5 flex items-end gap-2">
          <p className="text-4xl font-bold tracking-tight text-slate-900">
            {
              quota
                ?.remaining
              ?? 0
            }
          </p>

          <p className="pb-1 text-sm text-slate-500">
            of {
              quota
                ?.limit
              ?? 2
            } searches left
          </p>
        </div>


        <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-[#0A66C2] transition-all"
            style={{
              width:
                `${quota && quota.limit > 0
                  ? Math.max(
                      0,
                      Math.min(
                        100,
                        (quota.remaining / quota.limit) * 100
                      )
                    )
                  : 0}%`,
            }}
          />
        </div>


        <p className="mt-3 text-xs text-slate-500">
          Filters do not use another provider search.
        </p>

      </section>


      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">

        <div className="flex flex-wrap items-start justify-between gap-3">

          <div>

            <h2 className="text-xl font-semibold">
              Your Application Snapshot
            </h2>


            <p className="mt-1 text-sm text-gray-600">
              A quick view of your application activity, progression and response timing.
            </p>

          </div>


          <span className="rounded bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700">

            {
              opportunityAnalytics
                ?.tracked_opportunities
              ?? opportunities.length
            }{" "}
            saved roles

          </span>

        </div>


        {
          opportunityAnalytics === null
          ? (

            <div className="mt-5 rounded-lg border border-dashed p-4 text-sm text-gray-600">
              Application analytics are not available yet.
            </div>

          )
          : opportunityAnalytics
              .tracked_opportunities
            === 0
          ? (

            <div className="mt-5 rounded-lg border border-dashed p-4 text-sm text-gray-600">
              Track jobs to start building your application funnel.
            </div>

          )
          : (

            <div className="mt-5 space-y-6">

              <div>

                <p className="mb-3 text-xs font-medium uppercase tracking-wide text-gray-500">
                  Funnel
                </p>


                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">

                  <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">

                    <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">
                      Saved
                    </p>

                    <p className="mt-1 text-2xl font-semibold">
                      {
                        opportunityAnalytics
                          .tracked_opportunities
                      }
                    </p>

                  </div>


                  <div className="rounded-xl border border-sky-200 bg-sky-50 p-4">

                    <p className="text-xs font-semibold uppercase tracking-wide text-sky-700">
                      Applied
                    </p>

                    <p className="mt-1 text-2xl font-semibold">
                      {
                        opportunityAnalytics
                          .funnel
                          .applied
                      }
                    </p>

                  </div>


                  <div className="rounded-xl border border-indigo-200 bg-indigo-50 p-4">

                    <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">
                      OA
                    </p>

                    <p className="mt-1 text-2xl font-semibold">
                      {
                        opportunityAnalytics
                          .funnel
                          .oa
                      }
                    </p>

                  </div>


                  <div className="rounded-xl border border-violet-200 bg-violet-50 p-4">

                    <p className="text-xs font-semibold uppercase tracking-wide text-violet-700">
                      Interview
                    </p>

                    <p className="mt-1 text-2xl font-semibold">
                      {
                        opportunityAnalytics
                          .funnel
                          .interview
                      }
                    </p>

                  </div>


                  <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">

                    <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
                      Offer
                    </p>

                    <p className="mt-1 text-2xl font-semibold">
                      {
                        opportunityAnalytics
                          .funnel
                          .offer
                      }
                    </p>

                  </div>

                </div>

              </div>


              <div className="grid gap-6 lg:grid-cols-2">

                <div>

                  <p className="mb-3 text-xs font-medium uppercase tracking-wide text-gray-500">
                    Rates
                  </p>


                  <div className="grid grid-cols-2 gap-3 text-sm">

                    <div className="rounded-lg bg-gray-50 p-3">

                      <p className="text-xs text-gray-500">
                        Application rate
                      </p>

                      <p className="mt-1 text-lg font-semibold">
                        {
                          opportunityAnalytics
                            .rates
                            .application_rate_pct
                        }
                        %
                      </p>

                      <p className="mt-1 text-xs text-gray-500">
                        Applied ÷ saved roles
                      </p>

                    </div>


                    <div className="rounded-lg bg-gray-50 p-3">

                      <p className="text-xs text-gray-500">
                        Response rate
                      </p>

                      <p className="mt-1 text-lg font-semibold">
                        {
                          opportunityAnalytics
                            .rates
                            .response_rate_pct
                        }
                        %
                      </p>

                      <p className="mt-1 text-xs text-gray-500">
                        Responded ÷ applied
                      </p>

                    </div>


                    <div className="rounded-lg bg-gray-50 p-3">

                      <p className="text-xs text-gray-500">
                        OA rate
                      </p>

                      <p className="mt-1 text-lg font-semibold">
                        {
                          opportunityAnalytics
                            .rates
                            .oa_rate_pct
                        }
                        %
                      </p>

                      <p className="mt-1 text-xs text-gray-500">
                        OA ÷ applied
                      </p>

                    </div>


                    <div className="rounded-lg bg-gray-50 p-3">

                      <p className="text-xs text-gray-500">
                        Interview rate
                      </p>

                      <p className="mt-1 text-lg font-semibold">
                        {
                          opportunityAnalytics
                            .rates
                            .interview_rate_pct
                        }
                        %
                      </p>

                      <p className="mt-1 text-xs text-gray-500">
                        Interview ÷ applied
                      </p>

                    </div>


                    <div className="rounded-lg bg-gray-50 p-3">

                      <p className="text-xs text-gray-500">
                        Offer rate
                      </p>

                      <p className="mt-1 text-lg font-semibold">
                        {
                          opportunityAnalytics
                            .rates
                            .offer_rate_pct
                        }
                        %
                      </p>

                      <p className="mt-1 text-xs text-gray-500">
                        Offer ÷ applied
                      </p>

                    </div>


                    <div className="rounded-lg bg-gray-50 p-3">

                      <p className="text-xs text-gray-500">
                        Responses
                      </p>

                      <p className="mt-1 text-lg font-semibold">
                        {
                          opportunityAnalytics
                            .funnel
                            .responded
                        }
                      </p>

                      <p className="mt-1 text-xs text-gray-500">
                        Applications with a recorded response
                      </p>

                    </div>

                  </div>

                </div>


                <div>

                  <p className="mb-3 text-xs font-medium uppercase tracking-wide text-gray-500">
                    Average timing
                  </p>


                  <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">

                    <div className="rounded-lg bg-gray-50 p-3">

                      <p className="text-xs text-gray-500">
                        First response
                      </p>

                      <p className="mt-1 text-lg font-semibold">
                        {
                          opportunityAnalytics
                            .timing
                            .avg_days_to_response
                          === null
                            ? "—"
                            : `${opportunityAnalytics.timing.avg_days_to_response} days`
                        }
                      </p>

                    </div>


                    <div className="rounded-lg bg-gray-50 p-3">

                      <p className="text-xs text-gray-500">
                        Interview
                      </p>

                      <p className="mt-1 text-lg font-semibold">
                        {
                          opportunityAnalytics
                            .timing
                            .avg_days_to_interview
                          === null
                            ? "—"
                            : `${opportunityAnalytics.timing.avg_days_to_interview} days`
                        }
                      </p>

                    </div>


                    <div className="rounded-lg bg-gray-50 p-3">

                      <p className="text-xs text-gray-500">
                        Offer
                      </p>

                      <p className="mt-1 text-lg font-semibold">
                        {
                          opportunityAnalytics
                            .timing
                            .avg_days_to_offer
                          === null
                            ? "—"
                            : `${opportunityAnalytics.timing.avg_days_to_offer} days`
                        }
                      </p>

                    </div>

                  </div>

                </div>

              </div>


              <div className="grid gap-6 lg:grid-cols-2">

                <div>

                  <p className="mb-3 text-xs font-medium uppercase tracking-wide text-gray-500">
                    Current stage breakdown
                  </p>


                  {
                    opportunityAnalytics
                      .by_status
                      .length
                    === 0
                    ? (

                      <p className="text-sm text-gray-500">
                        No stage data yet.
                      </p>

                    )
                    : (

                      <div className="flex flex-wrap gap-2">

                        {
                          opportunityAnalytics
                            .by_status
                            .map(
                              (
                                item
                              ) => (

                                <span
                                  key={
                                    item
                                      .current_status
                                  }

                                  className="rounded bg-gray-100 px-3 py-2 text-sm text-gray-700"
                                >
                                  {
                                    formatText(
                                      item
                                        .current_status
                                    )
                                  }
                                  {": "}
                                  <strong>
                                    {
                                      item
                                        .count
                                    }
                                  </strong>
                                </span>

                              )
                            )
                        }

                      </div>

                    )
                  }

                </div>


                <div>

                  <p className="mb-3 text-xs font-medium uppercase tracking-wide text-gray-500">
                    Priority breakdown
                  </p>


                  {
                    opportunityAnalytics
                      .by_priority
                      .length
                    === 0
                    ? (

                      <p className="text-sm text-gray-500">
                        No priority data yet.
                      </p>

                    )
                    : (

                      <div className="flex flex-wrap gap-2">

                        {
                          opportunityAnalytics
                            .by_priority
                            .map(
                              (
                                item
                              ) => (

                                <span
                                  key={
                                    item
                                      .priority
                                  }

                                  className={
                                    "rounded px-3 py-2 text-sm "
                                    + getOpportunityPriorityClass(
                                      item
                                        .priority
                                    )
                                  }
                                >
                                  {
                                    formatText(
                                      item
                                        .priority
                                    )
                                  }
                                  {": "}
                                  <strong>
                                    {
                                      item
                                        .count
                                    }
                                  </strong>
                                </span>

                              )
                            )
                        }

                      </div>

                    )
                  }

                </div>

              </div>


              <p className="text-xs text-gray-500">
                These figures describe your recorded CareerCompass application history. They are not predictions of hiring outcomes.
              </p>

            </div>

          )
        }

      </section>




          </div>
        )
      }


      {
        activeView
        === "jobs"
        && (
          <div className="space-y-6 pt-6">

      <section id="careercompass-results" className="scroll-mt-4">

        <div className="mb-4">

          <div className="flex flex-wrap items-start justify-between gap-3">

            <div>

              <h2 className="text-2xl font-semibold">
                Job Matches
              </h2>


              <p className="text-sm text-gray-600">
                Showing {
                  visibleJobs.length
                } of {
                  jobs.length
                } jobs returned by this search
              </p>


              <button
                type="button"
                onClick={() => {
                  const searchPanel =
                    document.getElementById(
                      "careercompass-search"
                    ) as HTMLDetailsElement | null;

                  if (
                    searchPanel
                  ) {
                    searchPanel.open =
                      true;
                  }

                  searchPanel
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
                }}
                className="mt-2 text-left text-sm font-semibold text-[#0A66C2] hover:underline"
              >
                Looking for more opportunities? Search your desired role here (CLICK HERE)
              </button>

            </div>


            <div className="flex flex-wrap gap-2">

              <button
                type="button"
                onClick={() => {
                  const searchPanel =
                    document.getElementById(
                      "careercompass-search"
                    ) as HTMLDetailsElement | null;

                  if (
                    searchPanel
                  ) {
                    searchPanel.open =
                      true;
                  }

                  searchPanel
                    ?.scrollIntoView(
                      {
                        behavior: "smooth",
                        block: "center",
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
                }}
                className="rounded-lg bg-[#0A66C2] px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-[#004182]"
              >
                Search Another Role
              </button>


              {hasJobFilters && (

                <button
                  type="button"

                  onClick={() => {
                    setJobTypeFilter(
                      "all"
                    );

                    setJobStartMonthFilter(
                      "all"
                    );
                  }}

                  className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  Clear Filters
                </button>

              )}

            </div>

          </div>


          {jobs.length > 0 && (

            <div className="mt-4 grid gap-3 rounded-xl border border-blue-100 bg-blue-50/50 p-4 md:grid-cols-2">

              <div>

                <label className="text-xs font-medium uppercase tracking-wide text-gray-500">
                  Job type
                </label>


                <select
                  value={
                    jobTypeFilter
                  }

                  onChange={(event) =>
                    updateJobTypeFilter(
                      event.target.value
                    )
                  }

                  className="mt-2 w-full rounded border bg-white px-3 py-2 text-sm"
                >
                  <option value="all">
                    All job types
                  </option>

                  <option value="internship">
                    Internship
                  </option>

                  <option value="full_time">
                    Full-time
                  </option>

                  <option value="part_time">
                    Part-time
                  </option>

                  <option value="contract">
                    Contract / temporary
                  </option>

                  <option value="other">
                    Other / unspecified
                  </option>
                </select>

              </div>


              <div>

                <label className="text-xs font-medium uppercase tracking-wide text-gray-500">
                  Work start month
                </label>


                <select
                  value={
                    jobStartMonthFilter
                  }

                  onChange={(event) =>
                    setJobStartMonthFilter(
                      event.target.value
                    )
                  }

                  className="mt-2 w-full rounded border bg-white px-3 py-2 text-sm"
                >
                  <option value="all">
                    All / any start month
                  </option>

                  {
                    availableJobStartMonths.map(
                      (
                        month
                      ) => (
                        <option
                          key={
                            month
                          }
                          value={
                            month
                          }
                        >
                          {
                            formatStartMonth(
                              month
                            )
                          }
                        </option>
                      )
                    )
                  }

                  <option value="unknown">
                    Start month not stated
                  </option>
                </select>

              </div>


              <p className="text-xs text-gray-500 md:col-span-2">
                Job-type filtering uses the returned title/employment text. Start-month filtering is only applied when CareerCompass can identify an explicit start or intake month in the listing, so unstated dates remain under “Start month not stated”.
              </p>

            </div>

          )}

        </div>


        {
          jobs.length
          === 0
          ? (

            <div className="rounded-2xl border border-slate-200 bg-white p-6 text-slate-600 shadow-sm">
              No job results yet.
            </div>

          )
          : visibleJobs.length
            === 0
            ? (

              <div className="rounded-2xl border border-slate-200 bg-white p-6 text-slate-600 shadow-sm">
                No jobs match the current filters.
              </div>

            )
            : (

            <div className="space-y-4">

              {
                visibleJobs.map(
                  (
                    job
                  ) => (

                    <article
                      key={
                        job.job_id
                      }
                      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
                    >

                      <div className="flex flex-col justify-between gap-5 md:flex-row">

                        <div className="min-w-0 flex-1">

                          <h3 className="text-lg font-semibold text-slate-900">
                            {
                              job.raw_title
                            }
                          </h3>


                          {
                            cleanJobDescription(
                              job.description
                            )
                            && (
                              <p className="mt-4 max-w-3xl text-sm leading-6 text-slate-600">
                                {
                                  cleanJobDescription(
                                    job.description
                                  ).length
                                  > 320
                                    ? (
                                        cleanJobDescription(
                                          job.description
                                        ).slice(
                                          0,
                                          320
                                        ).trimEnd()
                                        + "…"
                                      )
                                    : cleanJobDescription(
                                        job.description
                                      )
                                }
                              </p>
                            )
                          }

                        </div>


                        <div className="flex h-fit flex-wrap gap-2 md:max-w-[360px] md:justify-end">

                          {
                            getTrackedOpportunity(
                              job.job_id
                            )
                            ? (
                              <button
                                type="button"
                                disabled
                                className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-800"
                              >
                                Saved · {
                                  formatText(
                                    getTrackedOpportunity(
                                      job.job_id
                                    )!
                                      .current_status
                                  )
                                }
                              </button>
                            )
                            : (
                              <button
                                type="button"
                                onClick={
                                  () =>
                                    handleTrackJob(
                                      job.job_id
                                    )
                                }
                                disabled={
                                  trackingJobId
                                  === job.job_id
                                }
                                className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#0A66C2] px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-[#004182] disabled:cursor-not-allowed disabled:opacity-50"
                              >
                                {
                                  trackingJobId
                                  === job.job_id
                                  && (
                                    <LoadingSpinner
                                      label="Saving job to My Applications"
                                    />
                                  )
                                }

                                {
                                  trackingJobId
                                  === job.job_id
                                    ? "Saving..."
                                    : "Save / Track"
                                }
                              </button>
                            )
                          }


                          <a
                            href={
                              job.job_url
                            }
                            target="_blank"
                            rel="noopener noreferrer"
                            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                          >
                            View Job Posting
                          </a>


                          <button
                            type="button"
                            onClick={() =>
                              sendJobToAnalyser(
                                job
                              )
                            }
                            className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-semibold text-[#0A66C2] hover:bg-blue-100"
                          >
                            Analyse Job
                          </button>

                        </div>

                      </div>

                    </article>

                  )
                )
              }

            </div>

          )
        }

      </section>

          </div>
        )
      }


      </div>

    </div>
  );
}
