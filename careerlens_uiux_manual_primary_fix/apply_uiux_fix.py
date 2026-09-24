#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()

FILES = {
    "manual": ROOT / "frontend/src/app/dashboard/manual-job-import.tsx",
    "header": ROOT / "frontend/src/app/dashboard/career-compass-header.tsx",
    "help": ROOT / "frontend/src/app/dashboard/career-compass-help.tsx",
    "dashboard": ROOT / "frontend/src/app/dashboard/dashboard-client.tsx",
}

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"{label}: expected exactly 1 matching block, found {count}. "
            "Your local file may differ from the current main branch."
        )
    return text.replace(old, new, 1)

def replace_n(text: str, old: str, new: str, n: int, label: str) -> str:
    count = text.count(old)
    if count < n:
        raise RuntimeError(
            f"{label}: expected at least {n} matching blocks, found {count}. "
            "Your local file may differ from the current main branch."
        )
    return text.replace(old, new, n)

for label, path in FILES.items():
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run this script from the CareerLens repo root."
        )

original = {key: path.read_text(encoding="utf-8") for key, path in FILES.items()}
updated = dict(original)

# 1 + 2 + 4: manual analyser is primary, always visible, with Upload Resume.

old = '''type ManualJobImportProps = {
  onOpportunitySaved?:
    () => Promise<void>;
};'''
new = '''type ManualJobImportProps = {
  onOpportunitySaved?:
    () => Promise<void>;

  onResumeUpload?:
    () => void;
};'''
updated["manual"] = replace_once(
    updated["manual"], old, new, "manual-job-import props"
)

old = '''export function ManualJobImport({
  onOpportunitySaved,
}: ManualJobImportProps) {
  const [
    open,
    setOpen,
  ] = useState(
    false
  );


  const ['''
new = '''export function ManualJobImport({
  onOpportunitySaved,
  onResumeUpload,
}: ManualJobImportProps) {
  const ['''
updated["manual"] = replace_once(
    updated["manual"], old, new, "remove manual analyser open/close state"
)

old = '''  return (
    <div
      id="careercompass-manual-job-import"
      className="mt-4 scroll-mt-6"
    >
      <button
        type="button"
        onClick={() =>
          setOpen(
            (
              current
            ) =>
              !current
          )
        }
        className="text-sm font-semibold text-white underline decoration-blue-200 underline-offset-4 transition hover:text-blue-100"
      >
        {
          open
            ? "Close job link"
            : (
              "Don’t see the role you want? "
              + "CLICK HERE and paste a job listing link to tailor your resume for it"
            )
        }
      </button>

      {
        open
        && (
          <div className="mx-auto mt-4 max-w-4xl rounded-2xl border border-white/25 bg-white p-5 text-left text-slate-900 shadow-2xl">

            <div>

              <h3 className="text-lg font-bold">
                Analyse a job from anywhere
              </h3>


              <p className="mt-1 text-sm text-slate-600">
                Paste a public job listing URL. Manual job imports do not use one of your two provider searches.
              </p>
            </div>'''
new = '''  return (
    <div
      id="careercompass-manual-job-import"
      className="mt-5 scroll-mt-6"
    >
      <div className="mx-auto max-w-4xl rounded-3xl border-2 border-white/70 bg-white p-5 text-left text-slate-900 shadow-2xl sm:p-6">

        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">

          <div>
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#0A66C2]">
              Primary job analyser
            </p>

            <h3 className="mt-1 text-2xl font-black tracking-tight">
              Analyse a job listing
            </h3>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              Paste a public job listing URL. CareerCompass will read the role, extract its requirements and help you compare them with your resume. Manual job imports do not use one of your two provider searches.
            </p>
          </div>

          <span className="w-fit rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-[#0A66C2]">
            Start here
          </span>

        </div>'''
updated["manual"] = replace_once(
    updated["manual"], old, new, "make manual analyser always visible"
)

old = '''              <div className="flex flex-col gap-2 sm:flex-row">
                <input
                  type="url"
                  value={
                    url
                  }
                  onChange={
                    (event) => {
                      setUrl(
                        event.target.value
                      );
                      resetImportedState();
                    }
                  }
                  placeholder="https://company.com/careers/job..."
                  required
                  className="min-h-11 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none ring-blue-200 focus:ring-2"
                />

                <button
                  type="submit"
                  disabled={
                    loading
                  }
                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#0A66C2] px-5 py-2.5 text-sm font-bold text-white shadow-sm hover:bg-[#004182] disabled:cursor-not-allowed disabled:opacity-50"
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

              </div>'''
new = '''              <div className="grid gap-2 lg:grid-cols-[minmax(0,1fr)_auto_auto]">
                <input
                  type="url"
                  value={
                    url
                  }
                  onChange={
                    (event) => {
                      setUrl(
                        event.target.value
                      );
                      resetImportedState();
                    }
                  }
                  placeholder="https://company.com/careers/job..."
                  required
                  className="min-h-11 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none ring-blue-200 focus:ring-2"
                />

                <button
                  type="submit"
                  disabled={
                    loading
                  }
                  className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-[#0A66C2] px-5 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-[#004182] disabled:cursor-not-allowed disabled:opacity-50"
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

                <button
                  type="button"
                  onClick={
                    onResumeUpload
                  }
                  disabled={
                    !onResumeUpload
                  }
                  className="min-h-11 rounded-lg border border-blue-200 bg-blue-50 px-5 py-2.5 text-sm font-bold text-[#0A66C2] shadow-sm transition hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Upload Resume
                </button>

              </div>'''
updated["manual"] = replace_once(
    updated["manual"], old, new, "add Upload Resume beside Read Job Listing"
)

old = '''          </div>
        )
      }

    </div>
  );
}'''
new = '''      </div>

    </div>
  );
}'''
updated["manual"] = replace_once(
    updated["manual"], old, new, "remove analyser visibility conditional closing"
)

# 2 + 5: manual analyser first, job search secondary.

old = '''  }


  function openResumeUpload() {'''
new = '''  }


  function scrollToManualJob() {
    document
      .getElementById(
        "careercompass-manual-job-import"
      )
      ?.scrollIntoView(
        {
          behavior:
            "smooth",
          block:
            "center",
        }
      );
  }


  function openResumeUpload() {'''
updated["header"] = replace_once(
    updated["header"], old, new, "add scrollToManualJob helper"
)

old = '''            onClick={
              scrollToSearch
            }'''
new = '''            onClick={
              scrollToManualJob
            }'''
updated["header"] = replace_n(
    updated["header"], old, new, 2, "point primary feature tiles to analyser"
)

old = '''        <div
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

        </div>'''
new = '''        <div className="mx-auto mt-9 max-w-4xl">

          <p className="text-sm font-semibold uppercase tracking-[0.14em] text-blue-100">
            Analyse a specific job
          </p>

          <ManualJobImport
            onOpportunitySaved={
              onOpportunitySaved
            }
            onResumeUpload={
              openResumeUpload
            }
          />


          <div
            id="careercompass-search"
            className="mt-7 scroll-mt-4 rounded-2xl border border-white/20 bg-[#061B35]/20 p-4 text-left backdrop-blur-sm"
          >

            <button
              type="button"
              onClick={
                scrollToSearch
              }
              className="text-sm font-semibold text-white underline decoration-blue-200 underline-offset-4 transition hover:text-blue-100"
            >
              Looking for more opportunities? Search your desired role here (CLICK HERE)
            </button>


            <form
              onSubmit={
                onSearch
              }
              className="mt-3 grid gap-3 rounded-2xl border border-white/15 bg-white/10 p-3 shadow-lg backdrop-blur-md md:grid-cols-[2fr_1fr_auto]"
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

          </div>

        </div>'''
updated["header"] = replace_once(
    updated["header"], old, new, "promote manual analyser and demote provider search"
)

# 3: update How to use.

old = '''              Use CareerCompass to find roles, understand what each role asks for, compare those requirements with your resume, and keep your applications organised.'''
new = '''              Use CareerCompass to analyse a specific job first, compare its requirements with your resume, discover more opportunities when needed, and keep your applications organised.'''
updated["help"] = replace_once(
    updated["help"], old, new, "update help intro"
)

old = '''              <HelpStep
                number="1"
                title="Upload your resume"
              >
                Start in <strong>My Profile</strong> and upload your resume. CareerCompass extracts profile evidence that is used when comparing you with job requirements.
              </HelpStep>

              <HelpStep
                number="2"
                title="Find a role"
              >
                Use <strong>Search Jobs</strong> to discover roles, or paste a public job listing link if you already have a specific role in mind. Manual job links do not use one of your two provider searches.
              </HelpStep>

              <HelpStep
                number="3"
                title="Review the role"
              >
                CareerCompass extracts the job requirements and separates search relevance from resume fit. A high search match means the role matches your search terms; it does not mean your resume is automatically a strong fit.
              </HelpStep>

              <HelpStep
                number="4"
                title="Compare the role with your resume"
              >
                Open the resume comparison to see what is <strong>Supported by your resume</strong>, <strong>Not shown on your resume</strong>, or <strong>Needs review</strong>. “Not shown” means CareerCompass did not find supporting evidence; it does not prove you do not have that skill.
              </HelpStep>

              <HelpStep
                number="5"
                title="Save and track the application"
              >
                Save roles to <strong>My Applications</strong>, move them through stages such as To Apply, Applied, Online Assessment, Interview and Offer, and record deadlines, follow-ups and other events.
              </HelpStep>

              <HelpStep
                number="6"
                title="Review your progress"
              >
                Use <strong>Career Insights</strong> to identify recurring requirement gaps and review your application activity over time.
              </HelpStep>'''
new = '''              <HelpStep
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
              </HelpStep>'''
updated["help"] = replace_once(
    updated["help"], old, new, "update recommended workflow"
)

old = '''                  Review jobs returned by your search, inspect extracted requirements, and save interesting roles.'''
new = '''                  Review roles returned by provider search, inspect their extracted requirements, and save interesting opportunities. Use the main analyser above when you already have a specific job listing.'''
updated["help"] = replace_once(
    updated["help"], old, new, "update Job Matches help description"
)

# 5: update Job Matches secondary CTA.

old = '''              <button
                type="button"
                onClick={() => {
                  document
                    .getElementById(
                      "careercompass-manual-job-import"
                    )
                    ?.scrollIntoView(
                      {
                        behavior:
                          "smooth",
                        block:
                          "center",
                      }
                    );
                }}
                className="mt-2 text-left text-sm font-semibold text-[#0A66C2] hover:underline"
              >
                Don&apos;t see the role you want? CLICK HERE and paste a job listing link to tailor your resume for it
              </button>'''
new = '''              <button
                type="button"
                onClick={() => {
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
                }}
                className="mt-2 text-left text-sm font-semibold text-[#0A66C2] hover:underline"
              >
                Looking for more opportunities? Search your desired role here (CLICK HERE)
              </button>'''
updated["dashboard"] = replace_once(
    updated["dashboard"], old, new, "update Job Matches search CTA"
)

# Validate all requested outcomes before writing.
assert "Close job link" not in updated["manual"]
assert "setOpen(" not in updated["manual"]
assert "onResumeUpload" in updated["manual"]
assert "Primary job analyser" in updated["manual"]
assert "Looking for more opportunities? Search your desired role here (CLICK HERE)" in updated["header"]
assert "Looking for more opportunities? Search your desired role here (CLICK HERE)" in updated["dashboard"]
assert 'title="Analyse the job you want"' in updated["help"]

changed = [key for key in FILES if updated[key] != original[key]]

if len(changed) != 4:
    raise RuntimeError(
        f"Expected 4 changed files, got {len(changed)}: {changed}"
    )

# All source anchors and outcome checks passed. Only now modify local files.
for key in changed:
    FILES[key].write_text(updated[key], encoding="utf-8")

print("UI/UX fix applied successfully:")
for key in changed:
    print(f"  - {FILES[key].relative_to(ROOT)}")

print()
print("Next:")
print("  cd frontend")
print("  npm run lint")
print("  npm run build")
print()
print("Review the changes with:")
print("  git diff")
