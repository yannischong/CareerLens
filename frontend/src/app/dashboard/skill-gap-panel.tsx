"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  createClient,
} from "@/lib/supabase/client";


type Coverage = {
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


type GapExample = {
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


type GapPriority = {
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
    GapExample[];
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
    Coverage;

  tier_counts: {
    A: number;
    B: number;
    C: number;
    D: number;
  };

  priority_count:
    number;

  priorities:
    GapPriority[];
};


type SkillGapPanelProps = {
  refreshKey:
    string;
};


function tierClass(
  tier:
    GapPriority[
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


function tierHeading(
  tier:
    GapPriority[
      "priority_tier"
    ]
) {
  if (tier === "A") {
    return (
      "Repeated profile gaps"
    );
  }


  if (tier === "B") {
    return (
      "Required profile gaps"
    );
  }


  if (tier === "C") {
    return (
      "Single-job signals"
    );
  }


  return (
    "Preferred-only signals"
  );
}


export default function SkillGapPanel({
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
          "rounded-lg border "
          + "bg-white p-6"
        }
      >
        <h2
          className={
            "text-xl "
            + "font-semibold"
          }
        >
          Skill Gap Intelligence
        </h2>

        <p
          className={
            "mt-2 "
            + "text-sm "
            + "text-gray-500"
          }
        >
          Analysing profile support
          across job requirements...
        </p>
      </section>
    );
  }


  if (error) {
    return (
      <section
        className={
          "rounded-lg border "
          + "bg-white p-6"
        }
      >
        <h2
          className={
            "text-xl "
            + "font-semibold"
          }
        >
          Skill Gap Intelligence
        </h2>

        <p
          className={
            "mt-2 "
            + "text-sm "
            + "text-red-600"
          }
        >
          {error}
        </p>
      </section>
    );
  }


  if (!analysis) {
    return null;
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
      GapPriority
  ) {
    return (
      <div
        key={
          `${gap.priority_tier}-`
          + `${gap.family_name}`
        }
        className={
          "rounded-lg "
          + "border p-4"
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
              Not currently supported
              by confirmed profile
              claims or evidence.
            </p>
          </div>

          <span
            className={
              "rounded-full "
              + "border px-2.5 "
              + "py-1 text-xs "
              + "font-medium "
              + tierClass(
                gap.priority_tier
              )
            }
          >
            Tier{" "}
            {gap.priority_tier}
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
              Why CareerCompass
              flagged this
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
      GapPriority[
        "priority_tier"
      ],

    gaps:
      GapPriority[],

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
            Tier {tier}
            {" — "}
            {tierHeading(
              tier
            )}
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
          Tier {tier}
          {" — "}
          {tierHeading(
            tier
          )}
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
        "rounded-lg border "
        + "bg-white p-6"
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
            Skill Gap Intelligence
          </h2>

          <p
            className={
              "mt-1 text-sm "
              + "text-gray-600"
            }
          >
            Profile-support gaps
            detected across your
            latest{" "}
            <strong>
              {analysis.query_text}
            </strong>
            {" "}
            search.
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
            sufficiently described
            jobs analyzed
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
          Coverage note
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
        A profile-support gap means
        your current CareerCompass
        profile does not contain
        confirmed evidence or a
        confirmed claim supporting
        that requirement. It does
        not mean you definitely lack
        the skill.
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