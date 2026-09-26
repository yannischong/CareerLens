# CareerCompass

CareerCompass is a full-stack career intelligence and application management platform that helps users discover relevant job opportunities, analyse what employers are looking for, compare those requirements against their current resume, and manage applications from discovery through follow-up.

The project combines job-search data, LLM-powered natural-language processing, deterministic matching, relational data modelling, resume evidence analysis, and application tracking in one workflow.

Rather than producing an opaque "chance of getting hired" score, CareerCompass keeps several analytical questions separate:

- **Search Relevance** — does the role match what the user searched for?
- **Data Quality** — is there enough listing information to assess the role?
- **Extracted Requirements** — what does the employer explicitly ask for?
- **Resume Evidence** — which requirements are supported by the current resume?
- **Eligibility** — does the listing state degree, student-status, work-authorisation, availability, or other prerequisites?
- **Career Insights** — which requirements and gaps recur across the user's target roles?

This keeps the analysis interpretable and avoids presenting uncertain screening outcomes as predictions.

---

## Live Application

https://careercompass-three-rosy.vercel.app

The deployed application supports:

- account creation and authentication
- private user workspaces
- job discovery through external providers
- CareerCompass Search → analyser handoff
- manual job URL analysis
- manual job-description fallback for provider pages that cannot be read reliably
- LLM-assisted requirement extraction
- hard-skill, soft-skill, and eligibility extraction
- resume upload and replacement
- resume-to-job comparison
- saved analysis snapshots
- application tracking
- application events and status history
- recurring skill-gap analysis
- multi-user data isolation
- provider-search quota controls

---

# Core Workflow

```text
Discover
   ↓
Analyse
   ↓
Understand Requirements
   ↓
Add to My Applications
   ↓
Compare Resume
   ↓
Apply
   ↓
Track
   ↓
Learn from Career Insights
```

Users can:

- search for job opportunities by role and location
- send a search result directly into the primary analyser
- open the original job posting from the analyser
- paste a public job-listing URL directly
- paste the full job description when a provider page cannot be read reliably
- extract hard skills, soft skills, and eligibility requirements
- add an analysed role directly to My Applications
- compare the role against the current resume immediately or later
- preserve saved analysis results without re-running extraction unnecessarily
- track application stages, events, notes, priorities, interviews, assessments, and follow-ups
- identify recurring requirements and resume gaps across saved roles

---

# Product Principles

## Evidence Over Assumptions

CareerCompass distinguishes between what the resume demonstrates and what the user may know outside the resume.

User-facing comparison language therefore uses categories such as:

```text
Supported by your resume
Not shown on your resume
Needs review
```

"Not shown" does not mean the user lacks the skill. It means CareerCompass could not find sufficient evidence in the current resume.

## Search Relevance Is Not Resume Fit

A job may be highly relevant to a search while being a weak resume match. Search relevance and resume evidence are therefore calculated and displayed separately.

## Eligibility Is Not Skill Fit

A candidate may have strong technical alignment but still face an explicit prerequisite such as:

- a particular degree or field of study
- a required year of study
- a graduation window
- a minimum internship commitment
- a required start date
- work-authorisation conditions
- language requirements
- certification, licence, registration, or clearance requirements

CareerCompass treats these as a separate analytical category rather than mixing them into hard-skill fit.

## Current Resume as the Source of Truth

Each profile maintains one current resume. Replacing the resume rebuilds the profile evidence used by future comparisons.

## Saved Analysis Should Be Reusable

Once a manually analysed listing is added to My Applications, CareerCompass stores the structured listing analysis. Saved applications can therefore reuse the same extracted requirements rather than spending model tokens to rediscover the same job requirements.

Resume-comparison snapshots can likewise be reused while the relevant resume remains current.

## The Analyser Is a Temporary Workspace

The primary analyser is intentionally transient. Refreshing or leaving the page clears the current unsaved analyser state, keeping the dashboard uncluttered.

The **Close Listing** action clears the currently loaded listing and analysis without deleting anything already stored in My Applications.

---

# Key Features

## 1. Authentication and Private Workspaces

CareerCompass uses Supabase Authentication.

Users can:

- create an account with email and password
- sign in and sign out
- maintain a private CareerCompass workspace

The backend identifies the user from the authenticated Supabase JWT rather than trusting a user ID supplied by the browser.

During the current development configuration, email confirmation is disabled so successful signup can proceed directly into the application.

---

## 2. Public Guest Dashboard

Unauthenticated visitors can preview the CareerCompass dashboard and product workflow, but API-backed actions remain locked until sign-in.

This allows users to understand the product before creating an account while keeping resumes, searches, applications, and analytics private.

---

## 3. CareerCompass Job Search

Users can search by role and location.

CareerCompass collects results from configured external job providers, including SerpAPI and Jooble, and normalises provider-specific responses into a shared job representation.

The search layer handles:

- provider-specific schemas
- duplicate listings
- inconsistent titles and descriptions
- source metadata
- company and location information
- original job URLs
- description-quality checks
- search relevance

### Search Quota

Authenticated accounts are protected by a provider-search quota guard. The current design limits each account to **two provider-backed searches**.

Manual listing analysis does not consume this provider-search quota.

---

## 4. Search → Primary Analyser Handoff

Search results are discovery tools rather than a separate application-saving workflow.

Selecting **Analyse Job** on a search result sends the role into the primary analyser and automatically carries across information such as:

- title
- company
- location
- source
- original job-posting URL

The analyser scrolls into view and provides **View Job Posting** so the user can open the source listing directly.

Search results are not saved directly from the search-results list. The user analyses the role first and explicitly adds it from the primary analyser.

---

## 5. Provider-Link Fallback

Some job-search provider links do not expose the complete job description reliably to the backend. Jooble listings are one example.

When a job is sent from CareerCompass Search into the analyser, CareerCompass therefore prompts the user:

> **Job found through CareerCompass Search —** Click **View Job Posting** and paste the full job description below, or find the official job listing on the company's website and paste its URL above.
>
> *Some job-search provider links, including Jooble listings, may not allow CareerLens to read the complete posting directly.*

This preserves the convenience of provider search while giving users a reliable path to analyse the employer's complete listing.

---

## 6. Primary Job Listing Analyser

The manual analyser is the main job-intelligence workspace.

Users can:

1. paste a public job URL, or receive one from CareerCompass Search
2. optionally paste the full job description
3. select **Read Job Listing**
4. inspect the extracted listing and requirements
5. open the original posting
6. add the analysed role to My Applications
7. compare it against the current resume
8. close the listing when finished

The analyser supports a description override because some public job pages are client-rendered, protected, incomplete, or routed through aggregators.

---

## 7. LLM-Powered Requirement Extraction

CareerCompass uses the OpenAI API as part of its NLP pipeline to convert unstructured job descriptions into structured requirements.

The current extraction surface is organised into three user-facing groups:

### Hard Skills

Examples:

```text
Python
SQL
Financial Modelling
Data Visualisation
Machine Learning
Bloomberg
```

### Soft Skills

Examples:

```text
Communication
Stakeholder Management
Problem Solving
Collaboration
```

### Eligibility

Examples include:

```text
Degree or field-of-study requirements
Year of study
Student status
Graduation year/window
Required experience
Internship duration
Minimum commitment period
Availability/start date
Work authorisation
Citizenship or sponsorship conditions
Language requirements
Certifications
Licences
Professional registrations
Security clearance
Physical prerequisites
```

---

## 8. Evidence-Grounded Eligibility Extraction

Eligibility previously relied mainly on deterministic pattern matching. The current implementation adds model-assisted extraction and verification.

The model is instructed to identify explicit eligibility, prerequisite, and logistical requirements and provide supporting evidence from the job description.

A model-produced eligibility item is accepted only when its evidence excerpt can be verified against the actual listing text. This is designed to improve coverage while reducing hallucinated prerequisites.

The deterministic extractor remains available as a fallback when model extraction is disabled or unavailable.

---

## 9. Atomic Concepts and Requirement Logic

Job requirements are normalised into reusable concepts rather than storing only full sentences.

For example:

```text
"Strong proficiency in SQL"
```

can map to:

```text
SQL
```

CareerCompass also supports logical requirement groups such as:

```text
ALL_OF
ANY_OF
```

For example:

```text
Python and SQL
```

can be represented as an `ALL_OF` group, while:

```text
Power BI or Tableau
```

can be represented as an `ANY_OF` group.

This gives downstream matching more structure than independent keyword detection.

---

## 10. Concept Normalisation and Aliases

Different employers may describe the same capability differently.

CareerCompass maintains concept normalisation and aliases so related wording can map onto a reusable taxonomy.

The matching pipeline distinguishes strong equivalences from weaker candidate relationships to reduce false positives.

---

## 11. Search Relevance

Search relevance answers:

> How closely does this listing correspond to the role the user searched for?

It does not answer:

> How qualified is the user?

CareerCompass uses TF-IDF representations of titles and descriptions. The documented combined score gives greater weight to title similarity than description similarity.

The full local environment can additionally support semantic ranking using Sentence Transformers.

---

## 12. Data Quality

A listing can be relevant to a search but still contain too little information for meaningful requirement analysis.

CareerCompass therefore distinguishes between a searchable listing and an assessable listing, reducing misleading extraction and fit results from incomplete descriptions.

---

## 13. Resume Upload and Replacement

Users maintain one current resume.

Supported processing includes formats such as PDF and DOCX. Resume files are stored privately using Supabase Storage.

When a resume is replaced:

```text
New resume uploaded
      ↓
Text parsed
      ↓
Previous derived evidence replaced
      ↓
Claims/evidence rebuilt
      ↓
Profile concepts refreshed
      ↓
Future comparisons use the new resume
```

This avoids mixing evidence from multiple outdated resumes.

---

## 14. Resume Evidence Mapping

Resume content is transformed into structured claims and evidence and mapped to the same concept vocabulary used by job requirements.

The matching system can use:

- direct concept matching
- aliases
- curated candidate relationships
- fuzzy matching
- semantic candidates where enabled
- model-assisted verification for manual-job comparisons

This provides a structured bridge between job requirements and resume evidence.

---

## 15. Resume Comparison

After a listing has been added to My Applications, the user can compare it against the current resume.

If **Compare Resume** is selected before the role has been added, CareerCompass explicitly asks the user to save the role first. Comparison does not silently create an application.

Once saved, the comparison categorises requirements into outcomes such as:

```text
Supported by your resume
Needs review
Not shown on your resume
```

CareerCompass does not interpret these categories as hiring probabilities.

---

## 16. Add to My Applications

The primary analyser contains an explicit **Add to My Applications** action.

The save workflow persists:

- the imported/normalised job
- the structured listing analysis
- the user's opportunity record
- the association between the authenticated profile and job

The save path is idempotent: saving an already-associated opportunity does not intentionally create duplicate application-tracking entries.

Search results themselves do not expose a separate Save/Track action; analysed jobs enter My Applications through the analyser.

---

## 17. Analysis Snapshots

CareerCompass stores manual listing analysis in:

```text
manual_job_analysis_snapshots
```

The snapshot can contain:

- structured listing analysis
- extracted requirements
- analysis version
- saved resume-fit analysis
- resume identifier

This supports a key product requirement:

> Opening a saved application should reuse the analysis already produced for that listing rather than automatically consuming more OpenAI tokens.

When the saved resume-fit snapshot corresponds to the current resume, it can be returned directly. A new comparison can be generated when the relevant resume changes.

---

## 18. Opportunity and Application Management

Saved opportunities can progress through stages including:

```text
Discovered
Saved
To Apply
Applied
Online Assessment
Interview
Offer
Rejected
Withdrawn
Closed
```

Users can also manage:

- priority
- notes
- application URL/method
- submission information
- referral information
- cover-letter information
- application events
- interviews
- assessments
- deadlines
- follow-ups

---

## 19. Application Events

CareerCompass stores chronological opportunity events such as:

```text
Created
Status change
Note
Deadline
Online assessment
Interview
Follow-up
Offer
Rejection
Withdrawal
Other
```

This provides a history of the user's interaction with each opportunity.

---

## 20. Career Insights and Skill-Gap Intelligence

CareerCompass aggregates requirements across saved opportunities to identify recurring patterns.

For example:

```text
SQL                8 roles
Power BI           6 roles
Python             5 roles
Statistics         5 roles
Stakeholder comms  4 roles
```

The goal is not to prescribe that every missing requirement must be learned. It is to reveal patterns in the specific roles the user is targeting.

---

## 21. Application Analytics

CareerCompass can aggregate information such as:

- applications by stage
- active opportunities
- upcoming events
- status progression
- recurring requirement gaps

This turns application tracking into structured career analytics rather than a simple list of jobs.

---

## 22. Loading and Interaction UX

Network-backed actions provide visible loading states and disable relevant controls while requests are active.

The dashboard includes feedback for operations such as:

- authentication
- workspace loading
- backend wake-up
- job search
- resume upload/replacement
- listing analysis
- adding an opportunity
- resume comparison
- status updates
- notes and application records
- application events
- Career Insights

The primary analyser also includes **Close Listing** to clear the active analysis and reduce dashboard clutter.

---

# Architecture

```text
                           ┌────────────────────┐
                           │        User        │
                           └─────────┬──────────┘
                                     │
                                     ▼
                           ┌────────────────────┐
                           │       Vercel       │
                           │ Next.js / React UI │
                           └─────────┬──────────┘
                                     │
                          Supabase JWT
                                     │
                                     ▼
                           ┌────────────────────┐
                           │       Render       │
                           │      FastAPI       │
                           └──────┬────┬────┬───┘
                                  │    │    │
                 ┌────────────────┘    │    └─────────────────┐
                 ▼                     ▼                      ▼
        ┌────────────────┐    ┌────────────────┐     ┌────────────────┐
        │   Supabase     │    │    OpenAI      │     │ External Job   │
        │   PostgreSQL   │    │      API       │     │   Providers    │
        └────────────────┘    │ NLP / LLM      │     │ SerpAPI/Jooble│
                 │            └────────────────┘     └────────────────┘
                 ▼
        ┌────────────────┐
        │ Supabase Auth  │
        │ + Storage      │
        └────────────────┘
```

---

# Technology Stack

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

## Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Uvicorn
- HTTPX

## NLP / LLM

- OpenAI API
- LLM-based structured requirement extraction
- evidence-grounded eligibility extraction
- deterministic/rule-based fallback extraction
- regular expressions
- text normalisation

## Database

- PostgreSQL
- Supabase

SQL is used extensively for:

- relational data modelling
- user/profile ownership
- job storage
- requirement relationships
- search records
- quotas
- resume metadata
- opportunities and applications
- event history
- analysis snapshots
- aggregation and analytics

## Authentication and Storage

- Supabase Auth
- JWT-authenticated backend requests
- Supabase private Storage for resumes
- Row Level Security on applicable Supabase tables

## Ranking and Matching

- scikit-learn
- TF-IDF
- cosine similarity
- RapidFuzz
- concept aliases
- deterministic matching
- curated candidate matching
- Sentence Transformers in the full local environment

## Job Collection

- SerpAPI
- Jooble
- public employer/job-listing URLs

## Infrastructure

- GitHub
- Vercel
- Render
- Supabase

---

# OpenAI Integration

CareerCompass uses OpenAI models for structured natural-language processing rather than sending raw model output directly to the UI.

A simplified extraction flow is:

```text
Job description
      ↓
Prompted structured extraction
      ↓
Hard skills
Soft skills
Eligibility
      ↓
Evidence / validation checks
      ↓
Normalised CareerCompass requirements
      ↓
Database snapshot
```

The model layer is therefore one component of a broader pipeline that also includes deterministic validation, taxonomy mapping, SQL persistence, resume evidence matching, and application-state management.

Environment configuration can select the model used for skill/requirement extraction.

If model extraction is unavailable, CareerCompass retains rule-based fallback behaviour for supported extraction paths.

---

# Production Deployment

```text
Frontend       → Vercel
Backend        → Render
Authentication → Supabase Auth
Database       → Supabase PostgreSQL
Resume Storage → Supabase Storage
LLM/NLP        → OpenAI API
```

The frontend and backend deploy independently. Frontend-only changes require a Vercel deployment; backend changes require a Render deployment. Database migrations are applied to Supabase separately.

---

# Production Matching Mode

The project supports a lighter production configuration to avoid loading the full local semantic-model stack on constrained hosting.

The full local environment can use Sentence Transformers and `all-MiniLM-L6-v2`.

With lightweight production mode enabled:

```text
Search ranking
→ TF-IDF-based scoring

Profile mapping
→ direct aliases
→ curated candidates
→ no local SentenceTransformer/PyTorch model required

Requirement extraction
→ OpenAI model when enabled
→ deterministic fallback where supported
```

This allows the deployed backend to retain LLM-powered extraction without carrying the memory cost of a local transformer embedding model.

---

# Current Pipelines

## Search Pipeline

```text
User submits role + location
        ↓
Authenticated request
        ↓
Quota guard
        ↓
Provider searches
        ↓
Normalisation / deduplication
        ↓
Description-quality assessment
        ↓
Search relevance
        ↓
Results displayed
        ↓
Analyse Job
        ↓
Primary analyser auto-filled
```

## Manual / Search-Handoff Analysis Pipeline

```text
URL entered manually
OR
Search result sent to analyser
        ↓
Optional full-description paste
        ↓
Read Job Listing
        ↓
URL validation / page extraction
        ↓
Description resolution
        ↓
LLM + fallback requirement extraction
        ↓
Hard Skills / Soft Skills / Eligibility
        ↓
Structured result displayed
        ↓
Add to My Applications
        ↓
Persist listing + analysis snapshot + opportunity
        ↓
Optional Compare Resume
```

## Saved Comparison Pipeline

```text
Saved opportunity opened
        ↓
Stored listing snapshot loaded
        ↓
Current resume identified
        ↓
Current matching snapshot exists?
        ├── Yes → reuse saved comparison
        └── No  → generate comparison and save snapshot
```

## Resume Pipeline

```text
Resume uploaded
        ↓
Document validated
        ↓
Text extracted
        ↓
Claims/evidence generated
        ↓
Previous current resume replaced
        ↓
Profile concept mapping rebuilt
        ↓
Future comparisons use new resume
```

---

# Backend API

Major FastAPI routes include:

## Profile

```text
GET /api/me
```

## Search

```text
POST /api/search
```

Search-related routes also support result retrieval, provider state, quota information, fit information, and eligibility information.

## Resumes

```text
GET  /api/resumes
POST /api/resumes
```

## Manual Jobs

```text
POST /api/manual-jobs/preview
POST /api/manual-jobs/import
GET  /api/manual-jobs
GET  /api/manual-jobs/{job_id}
GET  /api/manual-jobs/{job_id}/snapshot
POST /api/manual-jobs/{job_id}/analyze
```

The manual-job routes support previewing, importing, snapshot persistence, and cached/current-resume comparison.

## Opportunities

```text
GET    /api/opportunities
POST   /api/opportunities
GET    /api/opportunities/analytics

GET    /api/opportunities/{id}
PATCH  /api/opportunities/{id}
DELETE /api/opportunities/{id}

POST /api/opportunities/{id}/status
POST /api/opportunities/{id}/application
POST /api/opportunities/{id}/events
POST /api/opportunities/{id}/resume-comparison
```

## Analytics

Analytics routes derive user-level insights from saved opportunities and profile comparisons.

---

# Database Design

CareerCompass uses a relational PostgreSQL model.

Major entities include:

```text
auth.users
user_profiles

resume_documents
resume_sections
profile_claims
profile_evidence

jobs

search_requests
source_search_runs
source_search_results
user_search_quota

job_relevance_scores

job_requirements
requirement_groups
requirement_mentions
requirement_concepts
requirement_concept_aliases
job_requirement_concepts

profile_claim_concepts
profile_evidence_concepts
profile_fit_assessments

eligibility_facts
eligibility_checks

manual_job_imports
manual_job_analysis_snapshots
provider_analysis_cache

opportunities
applications
opportunity_events
```

The database is not merely storage for the web application; it is part of the analytical design. SQL relationships connect users, resumes, jobs, extracted concepts, evidence, saved opportunities, snapshots, and application history.

---

# Analysis Snapshot Persistence

The `manual_job_analysis_snapshots` table stores the structured result of manual listing analysis.

This table is important because CareerCompass should not repeatedly spend LLM tokens extracting the same listing every time the user opens a saved application.

Conceptually:

```text
Analyse listing
      ↓
Structured result generated
      ↓
User adds role
      ↓
Snapshot stored
      ↓
My Applications reuses snapshot
```

A resume-fit snapshot can also be associated with the resume used for the comparison. If the current resume changes, CareerCompass can determine that the previous comparison is no longer current.

---

# Authentication, Ownership, and Security

The Supabase authenticated user ID is the source of user ownership.

```text
auth.users.id
      ↓
user profile
      ↓
resume
      ↓
opportunities
      ↓
applications
      ↓
events / snapshots
```

The backend derives ownership from the authenticated JWT rather than trusting browser-supplied user identifiers.

Resume files are stored in a private Supabase Storage bucket.

Supabase Row Level Security is enabled for applicable user-sensitive tables, including the manual job analysis snapshot table in the production database.

Manual URL ingestion is performed server-side and includes checks intended to reduce server-side request-forgery risk.

---

# Environment Variables

## Backend

The backend uses environment variables such as:

```text
SUPABASE_URL
SUPABASE_PUBLISHABLE_KEY
SUPABASE_DATABASE_URL

SERPAPI_API_KEY
JOOBLE_API_KEY
JOOBLE_BASE_URL

OPENAI_API_KEY
CAREERLENS_MODEL_SKILL_EXTRACTION

LIGHTWEIGHT_MODE
PYTHON_VERSION
```

Exact environment-variable availability depends on the deployment configuration. Secrets must remain server-side and must not be committed.

## Frontend

```text
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
NEXT_PUBLIC_API_URL
```

Only values intended for browser use should use the `NEXT_PUBLIC_*` prefix.

---

# Local Development

## Backend

```bash
git clone <repository-url>
cd CareerLens

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

uvicorn api.index:app --reload
```

Local API:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

For local development, configure `frontend/.env.local` with the required public Supabase values and:

```text
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Frontend:

```text
http://localhost:3000
```

Before production deployment:

```bash
npm run lint
npm run build
```

---

# Database Migrations

Sequential schema migrations are stored under:

```text
sql/schema/
```

Additional feature-specific SQL files are also present under `sql/`, including the manual analysis snapshot schema.

Supabase-specific policies are stored separately where applicable.

When a code deployment introduces a new required table, the corresponding production Supabase migration must be applied before that code path is used.

---

# Repository Structure

```text
CareerLens/
│
├── api/
│   ├── auth.py
│   ├── index.py
│   ├── profile.py
│   ├── routes/
│   │   ├── analytics.py
│   │   ├── manual_jobs.py
│   │   ├── opportunities.py
│   │   ├── resumes.py
│   │   └── search.py
│   └── schemas/
│
├── src/
│   ├── cleaning/
│   ├── collection/
│   ├── eligibility/
│   ├── extraction/
│   ├── matching/
│   ├── ranking/
│   ├── requirements/
│   ├── services/
│   ├── taxonomy/
│   └── user_profile/
│
├── frontend/
│   └── src/app/
│       ├── dashboard/
│       └── login/
│
├── sql/
│   ├── schema/
│   ├── supabase/
│   ├── manual_job_analysis_snapshots.sql
│   └── provider_analysis_cache.sql
│
├── docs/
├── tests/
├── requirements.txt
├── requirements-render.txt
└── README.md
```

---

# Important Frontend Components

The dashboard includes components such as:

```text
career-compass-header.tsx
career-compass-help.tsx
application-pipeline.tsx
application-resume-comparison.tsx
manual-job-import.tsx
search-guidance.tsx
skill-gap-panel.tsx
loading-spinner.tsx
```

`dashboard-client.tsx` coordinates authenticated data loading, job-search state, resume state, opportunities, analytics, and UI refreshes after mutations.

The primary analyser (`manual-job-import.tsx`) coordinates:

- manual URL input
- Search → Analyse Job handoff
- description override
- listing preview
- extracted requirements
- Eligibility display
- Add to My Applications
- Compare Resume
- Close Listing

---

# Data and Analytics Skills Demonstrated

Although CareerCompass is a full-stack product, its core functionality is built around data and analytical problems.

## Python

Used for:

- backend services
- data processing
- text transformation
- extraction
- matching
- aggregation
- analytics

## SQL

Used for:

- relational modelling
- joins and filtering
- user ownership
- job/requirement relationships
- search tracking and quotas
- application tracking
- snapshot persistence
- aggregation and analytics

## NLP / LLM

Used for:

- converting unstructured job descriptions into structured requirements
- hard-skill extraction
- soft-skill extraction
- eligibility/prerequisite extraction
- evidence-grounded verification

## Data Cleaning and Integration

CareerCompass combines heterogeneous information from:

- multiple job providers
- employer/public job pages
- pasted job descriptions
- uploaded resumes
- authenticated profiles
- application histories

and converts it into a shared relational model.

## Text Analytics

The wider pipeline uses:

- normalisation
- regular expressions
- TF-IDF
- cosine similarity
- fuzzy matching
- semantic embeddings where enabled
- LLM extraction
- deterministic validation

## Taxonomy Design

Job requirements and resume evidence are mapped into reusable concepts, requiring decisions around:

- concept granularity
- synonyms
- equivalent terminology
- logical groups
- evidence thresholds
- false-positive prevention

## Analytical Interpretation

CareerCompass deliberately separates:

```text
Relevance
Data Quality
Requirements
Resume Evidence
Eligibility
```

rather than collapsing them into one arbitrary score.

---

# Software Engineering Skills Demonstrated

CareerCompass also demonstrates:

- REST API design
- frontend/backend separation
- authentication and JWT handling
- secure environment configuration
- relational database design
- schema migrations
- private file storage
- multi-user ownership
- state management
- asynchronous UI design
- API quota controls
- idempotent save operations
- analysis caching/snapshots
- cloud deployment
- production debugging
- Git/GitHub workflow
- CORS configuration

---

# Example Analysis

Suppose a listing contains:

```text
Requirements

- Strong SQL skills
- Experience with Python
- Experience with Power BI or Tableau
- Strong stakeholder communication
- Applicants must be penultimate-year students
- Able to commit to a 12-week internship
```

CareerCompass may extract:

```text
Hard Skills
- SQL
- Python
- Power BI OR Tableau

Soft Skills
- Stakeholder communication

Eligibility
- Penultimate-year student
- 12-week internship commitment
```

If the current resume contains:

```text
Technical Skills:
Python, SQL, Tableau

Experience:
Presented analysis to cross-functional stakeholders
```

the comparison may conceptually show:

```text
SQL
→ Supported by your resume

Python
→ Supported by your resume

Power BI OR Tableau
→ Supported through Tableau evidence

Stakeholder communication
→ Supported by experience evidence
```

Eligibility remains a separate listing requirement rather than being treated as a technical skill.

---

# Why CareerCompass Does Not Predict Hiring Probability

Hiring depends on variables CareerCompass cannot reliably observe, including:

- applicant competition
- recruiter preferences
- interview performance
- referrals
- internal candidates
- headcount changes
- role urgency
- employer-specific screening systems
- subjective assessment

A precise interview or offer probability would therefore imply unsupported certainty.

CareerCompass focuses on observable listing requirements and resume evidence instead.

---

# Current Limitations

## Public Job Page Variability

Job websites differ in HTML structure, client-side rendering, anti-bot protection, structured metadata, and description completeness.

Some provider URLs cannot be read reliably. CareerCompass therefore supports opening the source page and pasting the full description or replacing the provider URL with the official employer URL.

## LLM Extraction Is Not Infallible

Model-assisted extraction improves flexibility but can still miss or misinterpret ambiguous wording.

CareerCompass mitigates this with structured outputs, evidence verification for eligibility, normalisation, and deterministic fallback logic, but extracted requirements should still be treated as decision support rather than an authoritative employer interpretation.

## Production Semantic Matching

The lightweight deployed backend does not load the full local Sentence Transformer/PyTorch stack.

## Complex Requirement Cardinality

Conditions such as:

```text
At least 2 of the following 5 technologies
```

are not yet fully modelled.

## Resume Evidence Is Incomplete by Nature

CareerCompass only evaluates what is present in the uploaded resume. It cannot know undocumented skills or experiences.

## Provider Coverage

Search coverage depends on configured external providers and cannot represent every available job. Manual analysis exists partly to address this limitation.

---

# Future Development

Potential improvements include:

## Requirement Intelligence

- stronger requirement disambiguation
- richer eligibility classification
- more sophisticated evidence attribution
- cardinality-aware requirement groups
- additional model-evaluation tests

## Search

- additional providers
- improved deduplication
- company-level filters
- more search filters
- search history

## Resume Intelligence

- guided resume tailoring
- section-level recommendations
- achievement-quality analysis
- role-specific resume versions

## Career Insights

- requirement trends by occupation
- skill-demand breakdowns
- application conversion analytics
- time-to-stage metrics
- historical application performance

## Application Management

- automated reminders
- scheduled follow-ups
- calendar integration
- deadline notifications
- interview-preparation workflows

## Production Infrastructure

- stronger monitoring
- structured logging
- error tracking
- automated database migration workflow
- higher-memory backend hosting
- full production semantic model
- custom domain

---

# Project Status

CareerCompass is a deployed multi-user application supporting the current core workflow:

```text
Create account
      ↓
Upload current resume
      ↓
Discover or paste a job
      ↓
Read and analyse listing
      ↓
Extract Hard Skills / Soft Skills / Eligibility
      ↓
Add to My Applications
      ↓
Compare with current resume
      ↓
Track application progress
      ↓
Review Career Insights
```

The project has progressed from a local data-processing prototype into a deployed system combining:

```text
Job Discovery
+
NLP / LLM Requirement Extraction
+
Data Cleaning
+
SQL / Relational Modelling
+
Resume Evidence Mapping
+
Similarity and Concept Matching
+
Analysis Snapshotting
+
Application Tracking
+
Career Analytics
```

The central idea remains:

> Help users understand not only which opportunities are relevant, but what those opportunities explicitly require, what their current resume demonstrates, and what patterns emerge across the jobs they want.
