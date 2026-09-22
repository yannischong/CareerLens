"use client";


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


export type ApplicationPipelineOpportunity = {
  opportunity_id: number;
  current_status: OpportunityStatus;
  priority: OpportunityPriority;
  raw_title: string;
  raw_company_name: string;
  next_event_type: string | null;
  next_event_at: string | null;
};


type ApplicationPipelineColumn = {
  key: string;
  label: string;
  statuses: OpportunityStatus[];
  headerClass: string;
  countClass: string;
};


type ApplicationPipelineProps = {
  opportunities:
    ApplicationPipelineOpportunity[];
};


const columns:
  ApplicationPipelineColumn[] = [
    {
      key: "to_apply",
      label: "To Apply",
      statuses: [
        "discovered",
        "saved",
        "to_apply",
      ],
      headerClass:
        "border-amber-200 bg-amber-50 text-amber-900",
      countClass:
        "bg-amber-100 text-amber-800",
    },
    {
      key: "applied",
      label: "Applied",
      statuses: [
        "applied",
      ],
      headerClass:
        "border-sky-200 bg-sky-50 text-sky-900",
      countClass:
        "bg-sky-100 text-sky-800",
    },
    {
      key: "oa",
      label: "Online Assessment",
      statuses: [
        "oa",
      ],
      headerClass:
        "border-indigo-200 bg-indigo-50 text-indigo-900",
      countClass:
        "bg-indigo-100 text-indigo-800",
    },
    {
      key: "interview",
      label: "Interview",
      statuses: [
        "interview",
      ],
      headerClass:
        "border-violet-200 bg-violet-50 text-violet-900",
      countClass:
        "bg-violet-100 text-violet-800",
    },
    {
      key: "offer",
      label: "Offer",
      statuses: [
        "offer",
      ],
      headerClass:
        "border-emerald-200 bg-emerald-50 text-emerald-900",
      countClass:
        "bg-emerald-100 text-emerald-800",
    },
    {
      key: "closed",
      label: "Closed",
      statuses: [
        "rejected",
        "withdrawn",
        "closed",
      ],
      headerClass:
        "border-slate-200 bg-slate-50 text-slate-800",
      countClass:
        "bg-slate-200 text-slate-700",
    },
  ];


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
        character.toUpperCase()
    );
}


function formatDateTime(
  value: string
) {
  return new Date(
    value
  ).toLocaleString();
}


function priorityClass(
  priority:
    OpportunityPriority
) {
  if (
    priority === "high"
  ) {
    return (
      "bg-rose-50 text-rose-700"
    );
  }


  if (
    priority === "low"
  ) {
    return (
      "bg-slate-100 text-slate-700"
    );
  }


  return (
    "bg-blue-50 text-blue-700"
  );
}


export function ApplicationPipeline({
  opportunities,
}: ApplicationPipelineProps) {
  if (
    opportunities.length
    === 0
  ) {
    return null;
  }


  return (
    <div className="mt-6">

      <div className="flex flex-wrap items-end justify-between gap-3">

        <div>

          <h3 className="text-lg font-semibold text-slate-900">
            Application Pipeline
          </h3>


          <p className="mt-1 text-sm text-slate-600">
            See where every application stands at a glance. Upcoming deadlines and higher-priority roles stay prominent.
          </p>

        </div>


        <p className="text-xs text-slate-500">
          Select Manage to open the full application record.
        </p>

      </div>


      <div className="mt-4 overflow-x-auto pb-2">

        <div className="grid min-w-[1320px] grid-cols-6 gap-3">

          {
            columns.map(
              (
                column
              ) => {
                const columnOpportunities =
                  opportunities.filter(
                    (
                      opportunity
                    ) =>
                      column.statuses.includes(
                        opportunity.current_status
                      )
                  );


                return (
                  <div
                    key={
                      column.key
                    }
                    className="min-h-[210px] rounded-xl border border-slate-200 bg-slate-50/70 p-3"
                  >

                    <div
                      className={
                        "flex items-center justify-between gap-2 rounded-lg border px-3 py-2 "
                        + column.headerClass
                      }
                    >

                      <p className="text-sm font-semibold">
                        {
                          column.label
                        }
                      </p>


                      <span
                        className={
                          "rounded-full px-2 py-0.5 text-xs font-semibold "
                          + column.countClass
                        }
                      >
                        {
                          columnOpportunities.length
                        }
                      </span>

                    </div>


                    <div className="mt-3 space-y-3">

                      {
                        columnOpportunities.length
                        === 0
                        ? (
                          <div className="rounded-lg border border-dashed border-slate-200 bg-white/70 p-3 text-xs text-slate-400">
                            No applications here
                          </div>
                        )
                        : columnOpportunities.map(
                            (
                              opportunity
                            ) => (
                              <div
                                key={
                                  opportunity
                                    .opportunity_id
                                }
                                className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm"
                              >

                                <p className="line-clamp-2 text-sm font-semibold text-slate-900">
                                  {
                                    opportunity
                                      .raw_title
                                  }
                                </p>


                                <p className="mt-1 line-clamp-1 text-xs font-medium text-slate-600">
                                  {
                                    opportunity
                                      .raw_company_name
                                  }
                                </p>


                                <div className="mt-3 flex flex-wrap gap-1.5">

                                  <span
                                    className={
                                      "rounded-full px-2 py-1 text-[11px] font-semibold "
                                      + priorityClass(
                                          opportunity
                                            .priority
                                        )
                                    }
                                  >
                                    {
                                      formatText(
                                        opportunity
                                          .priority
                                      )
                                    }
                                  </span>


                                  {
                                    column.key
                                    === "to_apply"
                                    && (
                                      <span className="rounded-full bg-slate-100 px-2 py-1 text-[11px] text-slate-600">
                                        {
                                          formatText(
                                            opportunity
                                              .current_status
                                          )
                                        }
                                      </span>
                                    )
                                  }

                                </div>


                                {
                                  opportunity
                                    .next_event_at
                                  && (
                                    <div className="mt-3 rounded-lg bg-amber-50 px-2.5 py-2 text-[11px] text-amber-900">

                                      <span className="font-semibold">
                                        Next{" "}
                                        {
                                          opportunity
                                            .next_event_type
                                          ? formatText(
                                              opportunity
                                                .next_event_type
                                            )
                                          : "event"
                                        }
                                      </span>


                                      <span className="mt-0.5 block">
                                        {
                                          formatDateTime(
                                            opportunity
                                              .next_event_at
                                          )
                                        }
                                      </span>

                                    </div>
                                  )
                                }


                                <button
                                  type="button"
                                  onClick={() => {
                                    const target =
                                      document
                                        .getElementById(
                                          `application-${opportunity.opportunity_id}`
                                        );

                                    target
                                      ?.scrollIntoView(
                                        {
                                          behavior:
                                            "smooth",
                                          block:
                                            "start",
                                        }
                                      );
                                  }}
                                  className="mt-3 w-full rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-xs font-semibold text-[#0A66C2] hover:bg-blue-100"
                                >
                                  Manage
                                </button>

                              </div>
                            )
                          )
                      }

                    </div>

                  </div>
                );
              }
            )
          }

        </div>

      </div>

    </div>
  );
}
