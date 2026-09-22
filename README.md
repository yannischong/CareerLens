````markdown
# CareerCompass

CareerCompass is a full-stack career intelligence and application management platform that helps users discover relevant job opportunities, understand how their resume aligns with job requirements, tailor their application strategy, and manage the application process from discovery through follow-up.

The project addresses two related problems in modern job searching:

1. Finding relevant opportunities across fragmented job sources.
2. Understanding what employers are looking for in a resume, particularly as automated and AI-assisted screening tools are increasingly used before or alongside human review.

CareerCompass converts unstructured job listings and resume content into structured data that can be searched, compared, aggregated, and translated into actionable career insights.

Rather than producing an opaque "chance of getting hired" score, CareerCompass separates:

- Search Relevance
- Data Quality
- Profile Fit
- Eligibility
- Resume Evidence
- Career Insights

This keeps the analysis interpretable and avoids presenting uncertain screening outcomes as predictions.

---

## Live Application

**CareerCompass**

https://careercompass-three-rosy.vercel.app

**Backend API**

https://careercompass-api-2v4r.onrender.com

The deployed application supports:

- account creation and authentication
- private user workspaces
- job discovery
- manual job URL import
- resume upload and replacement
- job requirement extraction
- resume-to-job comparison
- application tracking
- application events
- recurring skill-gap analysis
- multi-user data isolation

---

# Core Workflow

CareerCompass is designed around the full job-search workflow:

```text
Discover
   ↓
Evaluate
   ↓
Prepare
   ↓
Apply
   ↓
Track
   ↓
Follow Up
   ↓
Analyse
   ↓
Improve
````

Users can:

* search for job opportunities by role and location
* import a public job listing using its URL
* upload one current resume
* extract structured requirements from job descriptions
* compare job requirements against resume evidence
* identify requirements already supported by their resume
* identify requirements not currently shown on their resume
* save opportunities
* track application stages
* record deadlines, interviews, assessments and follow-ups
* compare their current resume against previously saved applications
* identify recurring skill gaps across roles
* use these insights to improve future applications

---

# Why CareerCompass?

Job searching is often fragmented across several different activities.

A typical applicant may use:

* job boards to discover roles
* spreadsheets to track applications
* PDFs for resumes
* notes for interview progress
* job descriptions for skill requirements
* separate tools for resume analysis

This creates several problems.

## 1. Job discovery and resume preparation are disconnected

Finding a role does not immediately tell the applicant:

* which requirements matter
* which requirements are already supported by their resume
* which important requirements are not clearly demonstrated

CareerCompass connects the job listing directly to the user's current resume.

---

## 2. Job descriptions are largely unstructured

A listing may contain information about:

* technical skills
* tools
* education
* experience
* certifications
* languages
* domain knowledge
* eligibility
* preferred qualifications

CareerCompass extracts these into structured requirements that can be analysed programmatically.

---

## 3. Resume feedback is often too simplistic

A single "resume score" can hide important distinctions.

CareerCompass instead asks:

```text
Is the job relevant to the search query?

Is the job description detailed enough to assess?

What requirements does the employer state?

Which requirements are supported by evidence in the resume?

Which requirements are not currently shown?

Are there explicit eligibility conditions?

Which missing requirements recur across multiple roles?
```

---

## 4. Missing evidence is not necessarily a missing skill

CareerCompass deliberately uses wording such as:

```text
Supported by your resume
```

and:

```text
Not shown on your resume
```

rather than claiming that the user does or does not possess a skill.

A resume is evidence, not a complete representation of a person.

---

# Product Principles

CareerCompass was designed around several principles.

## Evidence Over Assumptions

A requirement is considered supported only when sufficient evidence can be identified in the user's resume.

If evidence cannot be found, CareerCompass reports that the requirement is:

```text
Not shown on your resume
```

This does not imply that the user lacks the skill.

---

## Search Relevance Is Not Resume Fit

A job may be highly relevant to a search such as:

```text
Data Analyst Intern
```

even if the current resume is not a strong match.

CareerCompass therefore keeps:

```text
Search Relevance
```

separate from:

```text
Profile Fit
```

---

## Transparent Matching

CareerCompass exposes understandable categories rather than attempting to provide a single opaque hiring probability.

---

## Current Resume as the Source of Truth

Each user maintains one current resume.

When a new resume is uploaded:

```text
Existing resume
      ↓
Replaced
      ↓
New resume parsed
      ↓
Profile evidence rebuilt
      ↓
Future comparisons use latest resume
```

This prevents outdated resumes from being mixed together when assessing a role.

---

## Analysis Should Lead to Action

CareerCompass is not intended only to display scores.

The goal is to help users answer:

```text
What should I highlight?

What is already demonstrated?

What is missing from my resume?

Which skills keep appearing across the jobs I want?

Where should I focus my preparation?
```

---

# Key Features

## 1. Public Guest Dashboard

Users who visit CareerCompass without signing in are taken to the main CareerCompass dashboard rather than directly to an authentication screen.

The guest dashboard provides a preview of the product while keeping all functionality locked.

Unauthenticated users can see:

* CareerCompass branding
* job search interface
* resume upload interface
* workspace categories
* product workflow

However:

* search is disabled
* resume upload is disabled
* application data is unavailable
* API-backed functionality is unavailable

Users must select:

```text
Sign up / Log in
```

before using CareerCompass.

---

# 2. Authentication

CareerCompass uses Supabase Authentication.

Users can:

* create an account
* sign in
* sign out
* maintain their own private workspace

Account creation requires:

```text
Email
Password
Confirm Password
```

The frontend verifies that both password fields match before submitting the signup request.

The backend identifies users from their authenticated Supabase JWT rather than trusting a user ID supplied by the browser.

---

# 3. Job Discovery

Users can search by:

```text
Role
Location
```

Example:

```text
Role:
Data Analyst Intern

Location:
Singapore
```

CareerCompass collects results from configured external job providers and transforms them into a common internal representation.

The system handles:

* provider-specific schemas
* duplicate listings
* inconsistent titles
* inconsistent descriptions
* source metadata
* location information
* company names
* job URLs

---

# 4. Search Relevance

Search results are ranked by relevance to the user's query.

Search relevance answers:

> How closely does this job correspond to what the user searched for?

It does not answer:

> How qualified is the user for this job?

These are deliberately separate measurements.

---

## TF-IDF Ranking

CareerCompass uses TF-IDF representations for:

* job titles
* job descriptions

The query is compared with both.

The current combined score uses:

```text
65% title similarity
35% description similarity
```

This gives job titles greater influence because they are generally a stronger indicator of whether the role matches the requested occupation.

---

## Semantic Ranking

The local development environment additionally supports semantic ranking using:

```text
sentence-transformers/all-MiniLM-L6-v2
```

This allows semantically related phrases to receive similarity even when they do not use identical words.

---

# 5. Data Quality

Not every job listing contains enough information for meaningful resume analysis.

CareerCompass therefore distinguishes between:

```text
searchable job
```

and:

```text
assessable job
```

A job can still be relevant to the query while lacking enough description content for reliable requirement extraction.

The system currently uses a minimum description threshold when determining whether a listing contains enough information for assessment.

This helps prevent:

* misleading fit scores
* requirement extraction from extremely short descriptions
* false conclusions from incomplete listings

---

# 6. Manual Job URL Import

Not every role a user wants will appear through CareerCompass's providers.

Users can therefore paste the URL of a public job listing directly into CareerCompass.

Example workflow:

```text
Public job URL
      ↓
Fetch page
      ↓
Extract listing
      ↓
Normalise job
      ↓
Extract requirements
      ↓
Compare with current resume
      ↓
Optionally save to applications
```

The manual importer supports general public job pages and includes additional handling for supported structured job platforms.

---

## Manual Import Security

Because the backend fetches user-provided URLs, manual job import includes checks intended to reduce server-side request forgery risk.

Public job URLs are processed by the backend rather than exposing provider logic directly to the browser.

---

# 7. Job Normalisation

Jobs from different sources are transformed into a shared schema.

Normalisation includes fields such as:

* raw title
* normalised title
* raw company name
* description
* normalised description
* source
* source-specific job ID
* job URL
* location

This provides a consistent foundation for downstream analysis.

---

# 8. Requirement Extraction

CareerCompass converts job descriptions into structured job requirements.

Requirements may include:

```text
Skills
Tools
Domain knowledge
Education
Experience
Languages
Certifications
Licences
Professional registrations
Eligibility conditions
```

Example job description:

```text
Applicants should have experience with SQL,
Python and data visualisation.
Knowledge of Power BI or Tableau is preferred.
```

CareerCompass attempts to transform this into structured concepts such as:

```text
SQL
Python
Data visualisation

Power BI OR Tableau
```

---

# 9. Atomic Requirement Concepts

Requirements are normalised into atomic concepts.

For example:

```text
"Proficiency in SQL is required"
```

becomes:

```text
SQL
```

rather than storing the entire sentence as the concept.

This makes it possible to compare requirements across:

* different companies
* different wording
* different job listings

---

## Concept Types

CareerCompass can classify concepts into types including:

```text
skill
tool
domain_knowledge
language
education
certification
licence
professional_registration
```

---

# 10. Concept Aliases

Different organisations may describe the same capability differently.

CareerCompass maintains aliases and normalisation rules.

Examples include relationships such as:

```text
data cleansing
↔
data cleaning
```

and:

```text
AWS Bedrock
↔
Amazon Bedrock
```

Some aliases are treated as sufficiently strong equivalences to count as confirmed evidence.

Other relationships are intentionally treated only as candidate matches requiring caution.

---

# 11. Requirement Logic

Requirements are not always independent.

CareerCompass supports logical requirement groups including:

```text
ALL_OF
```

and:

```text
ANY_OF
```

Example:

```text
Experience with Python and SQL
```

can be represented as:

```text
ALL_OF
├── Python
└── SQL
```

while:

```text
Experience with Power BI or Tableau
```

can be represented as:

```text
ANY_OF
├── Power BI
└── Tableau
```

This is more accurate than treating every keyword in a job description as an independent mandatory requirement.

---

# 12. Resume Upload

Users upload their current resume through CareerCompass.

Supported document processing includes formats such as:

```text
PDF
DOCX
```

Resume files are stored privately using Supabase Storage.

---

# 13. Single Current Resume Model

CareerCompass intentionally allows one active resume per profile.

When a user uploads a replacement:

```text
New document parsed
      ↓
Existing resume identified
      ↓
Previous resume removed
      ↓
Derived evidence removed
      ↓
New resume stored
      ↓
New claims created
      ↓
New evidence created
      ↓
Profile concepts rebuilt
```

The database enforces one current resume per profile.

This prevents comparisons from accidentally using evidence across several outdated resumes.

---

# 14. Resume Parsing

CareerCompass extracts information from the uploaded resume and converts it into structured profile information.

Examples include:

```text
Skills
Languages
Experience
Projects
Education
Certifications
Other evidence
```

The extracted information is divided into:

```text
Profile Claims
```

and:

```text
Profile Evidence
```

These structures are used when comparing the user against job requirements.

---

# 15. Resume Concept Mapping

CareerCompass maps resume evidence onto the same concept vocabulary used for job requirements.

The mapper uses multiple layers.

## Direct Matching

Direct aliases can produce confirmed matches.

Example:

```text
Job requirement:
SQL

Resume:
Python, SQL, Tableau
```

Result:

```text
SQL → confirmed
```

---

## Curated Candidate Matching

Some related concepts are intentionally treated more cautiously.

Example:

```text
Job requirement:
Statistical analysis

Resume:
Analysed data for...
```

These may be surfaced as candidate evidence rather than automatically treated as proof.

---

## Semantic Candidates

The full local version can use sentence embeddings to identify semantically related evidence.

Semantic matches are intentionally treated as candidates rather than unquestionable proof.

---

# 16. Profile Fit

Profile Fit evaluates job requirements against evidence found in the user's current resume.

It answers:

> How much of this job's extracted requirement set is supported by the resume?

It does not represent:

```text
Probability of interview
Probability of passing ATS
Probability of receiving an offer
Recruiter score
```

---

# 17. Resume Comparison

Users can open a resume comparison for a role.

CareerCompass divides requirements into user-facing categories.

## Supported by Your Resume

CareerCompass identified sufficiently strong evidence corresponding to the requirement.

---

## Not Shown on Your Resume

CareerCompass could not identify sufficient evidence for the requirement in the current resume.

This wording is intentional.

It does not mean:

```text
You do not know this skill.
```

It means:

```text
CareerCompass could not find evidence of this requirement
in the resume currently being assessed.
```

---

## Needs Review

CareerCompass found potentially related evidence, but the relationship is not strong enough to automatically classify as confirmed.

---

# 18. Current-Resume Comparison for Saved Applications

Resume comparison is available for saved opportunities regardless of whether the role originated from:

* provider search
* manual URL import

Comparisons are generated against the user's current resume.

This means that when the user improves or replaces their resume, they can reopen an older application and evaluate it against the latest version.

---

# 19. Eligibility

Eligibility is assessed separately from profile fit.

Eligibility can include explicit conditions such as:

* graduation year
* student status
* degree requirements
* work authorisation
* programme requirements

Separating eligibility from fit prevents a candidate from appearing highly suitable purely because their resume contains the right skills when they may not satisfy an explicit application condition.

---

# 20. Opportunity Management

CareerCompass allows users to save and manage opportunities.

Current opportunity stages include:

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

Each opportunity is associated with the authenticated user's profile.

---

# 21. Application Records

Applications can contain information such as:

* resume used
* application URL
* application method
* submission date
* referral information
* cover-letter information
* notes

---

# 22. Application Events

CareerCompass stores an event history for each opportunity.

Supported event types include:

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

This produces a chronological timeline of the user's interaction with the opportunity.

---

# 23. Priority and Follow-Up Management

Users can assign opportunity priorities such as:

```text
Low
Medium
High
```

CareerCompass can also store upcoming event information to help users identify:

* application deadlines
* interviews
* assessments
* follow-up dates

---

# 24. Career Insights

CareerCompass provides both tactical and strategic analysis.

## Tactical Analysis

For an individual job:

```text
What does this role require?

What does my resume already support?

What is not currently shown?

What should I consider highlighting?
```

---

## Strategic Analysis

Across saved opportunities:

```text
Which requirements keep appearing?

Which skills repeatedly appear as gaps?

Which areas may be worth learning or highlighting?
```

This is exposed through Career Insights / Skills to Build.

---

# 25. Skill Gap Intelligence

Recurring requirements are aggregated across the user's saved opportunities.

This allows CareerCompass to identify patterns that would be difficult to notice by reading each job description individually.

For example:

```text
SQL                8 roles
Power BI           6 roles
Python             5 roles
Statistics         5 roles
Stakeholder comms  4 roles
```

The purpose is not to say:

```text
You must learn everything.
```

Instead, it helps users understand the demand patterns within the particular jobs they are targeting.

---

# 26. Application Analytics

CareerCompass can aggregate application pipeline information to help users understand their activity.

Examples include:

* applications by stage
* active opportunities
* upcoming events
* status progression
* recurring gaps

This connects the job-search process with structured analytics rather than treating every application independently.

---

# 27. Loading and Interaction UX

CareerCompass includes explicit loading states for asynchronous operations.

These include:

* account authentication
* account creation
* workspace loading
* backend wake-up
* job search
* resume upload
* resume replacement
* manual job import
* resume comparison
* saving opportunities
* updating opportunity stages
* updating priority
* saving notes
* recording application details
* creating application events
* loading application histories
* deleting applications
* loading Career Insights
* signing out

Buttons are disabled while relevant requests are running to reduce accidental duplicate submissions.

---

# 28. Dark Mode Support

Authentication and dashboard interfaces include explicit dark-mode styling for:

* text
* labels
* inputs
* borders
* cards
* errors
* loading states

The interface therefore does not rely on light-mode browser assumptions.

---

# Architecture

The deployed system follows this structure:

```text
                        ┌────────────────────┐
                        │       User         │
                        └─────────┬──────────┘
                                  │
                                  ▼
                        ┌────────────────────┐
                        │       Vercel       │
                        │      Next.js       │
                        │      Frontend      │
                        └─────────┬──────────┘
                                  │
                      Supabase JWT│
                                  ▼
                        ┌────────────────────┐
                        │       Render       │
                        │      FastAPI       │
                        │      Backend       │
                        └─────────┬──────────┘
                                  │
             ┌────────────────────┼─────────────────────┐
             │                    │                     │
             ▼                    ▼                     ▼
    ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
    │   Supabase     │   │   Supabase     │   │ External Job   │
    │   PostgreSQL   │   │ Private Storage│   │   Providers    │
    └────────────────┘   └────────────────┘   └────────────────┘
             ▲
             │
             ▼
    ┌────────────────┐
    │ Supabase Auth  │
    └────────────────┘
```

---

# Technology Stack

## Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS

---

## Backend

* Python
* FastAPI
* SQLAlchemy
* Pydantic
* Uvicorn
* HTTPX

---

## Database

* PostgreSQL
* Supabase

---

## Authentication

* Supabase Auth
* JWT-based authenticated backend requests

---

## File Storage

* Supabase private Storage

---

## Data Processing

* pandas
* NumPy
* regular expressions
* custom cleaning pipelines
* structured requirement extraction

---

## Matching and Ranking

* scikit-learn
* TF-IDF
* cosine similarity
* RapidFuzz
* concept aliases
* deterministic matching
* curated candidate matching
* Sentence Transformers in the full local environment

---

## Job Collection

* external job APIs
* SerpAPI
* Jooble
* public job listing URLs

---

## Infrastructure

* GitHub
* Vercel
* Render
* Supabase

---

# Production Deployment

CareerCompass is currently deployed using:

```text
Frontend
Vercel

Backend
Render

Authentication
Supabase Auth

Database
Supabase PostgreSQL

Resume Storage
Supabase Storage
```

---

# Production Lightweight Mode

The full local CareerCompass environment supports:

```text
sentence-transformers
PyTorch
all-MiniLM-L6-v2
```

The free Render backend has a limited memory allocation.

Loading PyTorch and Sentence Transformers exceeded the available production memory during initial deployment.

CareerCompass therefore supports:

```text
LIGHTWEIGHT_MODE=true
```

in production.

---

## Full Local Mode

```text
Search ranking
→ TF-IDF + semantic embeddings

Profile mapping
→ direct aliases
→ curated aliases
→ semantic candidates
```

---

## Lightweight Production Mode

```text
Search ranking
→ TF-IDF-based scoring

Profile mapping
→ direct aliases
→ curated candidates
→ no SentenceTransformer model loaded
```

This prevents the production backend from importing PyTorch and its large runtime dependency stack.

The full semantic implementation remains available locally.

---

# Search Pipeline

A simplified search request follows:

```text
User submits search
        ↓
Authenticated request
        ↓
Search request recorded
        ↓
Provider searches executed
        ↓
Raw provider results collected
        ↓
Jobs normalised
        ↓
Duplicates handled
        ↓
Description quality assessed
        ↓
Relevance scores generated
        ↓
Requirements extracted
        ↓
Current resume compared
        ↓
Eligibility assessed
        ↓
Results returned to frontend
```

---

# Manual Job Pipeline

```text
User pastes public listing URL
        ↓
Backend validates URL
        ↓
Listing fetched
        ↓
Structured page information extracted
        ↓
Job normalised
        ↓
Requirements extracted
        ↓
Atomic concepts generated
        ↓
Current resume compared
        ↓
Result displayed
        ↓
User can save to applications
```

---

# Resume Pipeline

```text
User uploads resume
        ↓
Document validated
        ↓
Text extracted
        ↓
Sections identified
        ↓
Claims extracted
        ↓
Evidence extracted
        ↓
Previous resume replaced
        ↓
Concept mapping rebuilt
        ↓
Profile facts refreshed
        ↓
Future comparisons use new resume
```

---

# Application Pipeline

```text
Opportunity discovered/imported
        ↓
Saved
        ↓
To Apply
        ↓
Applied
        ↓
Online Assessment
        ↓
Interview
        ↓
Offer / Rejected / Withdrawn
```

Events can be recorded throughout the process.

---

# Backend API

The FastAPI backend exposes endpoints for the major CareerCompass workflows.

## Profile

```text
GET /api/me
```

Returns the authenticated user's CareerCompass profile information.

---

## Search

```text
POST /api/search
```

Creates a job search.

Additional search endpoints support:

* search results
* search state
* quota information
* fit data
* eligibility data

---

## Resumes

```text
GET  /api/resumes
POST /api/resumes
```

Supports:

* retrieving the current resume
* uploading a resume
* replacing the existing resume
* rebuilding the user profile

---

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

---

## Manual Jobs

Manual-job endpoints support:

* URL ingestion
* listing extraction
* requirement extraction
* current-resume comparison
* opportunity creation

---

## Analytics

Analytics endpoints provide CareerCompass insight data derived from saved opportunities and profile comparisons.

---

# Database Design

CareerCompass uses a relational PostgreSQL data model.

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

job_relevance_scores

job_requirements
requirement_groups

requirement_concepts
requirement_concept_aliases
job_requirement_concepts

profile_claim_concepts
profile_evidence_concepts

profile_fit_assessments

eligibility_facts
eligibility_checks

opportunities
applications
opportunity_events

manual_job_imports
```

---

# Authentication and Ownership

The Supabase authenticated user ID is the source of ownership.

Conceptually:

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
events
```

The backend determines ownership from the authenticated JWT.

Client-supplied user IDs are not trusted as proof of ownership.

---

# User Isolation

CareerCompass was tested with multiple accounts.

A second authenticated user:

* cannot access the first user's resume
* cannot access the first user's opportunities
* cannot access the first user's application events
* cannot access the first user's Career Insights
* receives a separate private workspace

---

# Resume Storage Security

Resume files are stored in a private Supabase Storage bucket.

Storage access is tied to authenticated user ownership.

Resume documents are not intended to be publicly accessible.

---

# Environment Variables

## Backend

The Render backend uses environment variables such as:

```text
SUPABASE_URL
SUPABASE_PUBLISHABLE_KEY
SUPABASE_DATABASE_URL

SERPAPI_API_KEY
JOOBLE_API_KEY
JOOBLE_BASE_URL

LIGHTWEIGHT_MODE
PYTHON_VERSION
```

Secrets are not exposed to the frontend.

---

## Frontend

The Vercel frontend uses:

```text
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
NEXT_PUBLIC_API_URL
```

Example production API configuration:

```text
NEXT_PUBLIC_API_URL=https://careercompass-api-2v4r.onrender.com
```

Only values intended for browser use are exposed through `NEXT_PUBLIC_*`.

Database passwords and provider API keys remain server-side.

---

# Local Development

## 1. Clone the Repository

```bash
git clone <repository-url>
cd CareerLens
```

---

## 2. Create a Python Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

---

## 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create the local environment file required by the backend and provide the necessary Supabase and provider credentials.

Do not commit production secrets.

---

## 5. Run the Backend

```bash
uvicorn api.index:app --reload
```

Local API:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

---

# Frontend Development

Move into:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Configure:

```text
frontend/.env.local
```

with variables such as:

```text
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
NEXT_PUBLIC_API_URL
```

For local development:

```text
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

Run:

```bash
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

# Frontend Validation

Run:

```bash
npm run lint
```

and:

```bash
npm run build
```

before production deployment.

---

# Database Migrations

Schema migrations are stored under:

```text
sql/schema/
```

The project currently maintains sequential SQL migrations for features including:

* core tables
* search infrastructure
* job normalisation
* requirements
* concept mapping
* profile evidence
* profile fit
* eligibility
* opportunity management
* application events
* manual job import
* single-resume enforcement

Supabase-specific policies are stored separately under:

```text
sql/supabase/
```

---

# Production Build Dependencies

The full development environment uses:

```text
requirements.txt
```

The lightweight Render deployment uses:

```text
requirements-render.txt
```

The production requirements intentionally exclude:

```text
sentence-transformers
PyTorch
Jupyter
CUDA libraries
```

to remain within the memory constraints of the free backend host.

---

# Repository Structure

A simplified representation of the repository:

```text
CareerLens/
│
├── api/
│   ├── auth.py
│   ├── index.py
│   ├── profile.py
│   │
│   ├── routes/
│   │   ├── analytics.py
│   │   ├── manual_jobs.py
│   │   ├── opportunities.py
│   │   ├── resumes.py
│   │   └── search.py
│   │
│   └── schemas/
│
├── src/
│   ├── cleaning/
│   ├── collection/
│   ├── eligibility/
│   ├── ranking/
│   ├── requirements/
│   ├── services/
│   ├── taxonomy/
│   └── user_profile/
│
├── frontend/
│   └── src/
│       └── app/
│           ├── dashboard/
│           └── login/
│
├── sql/
│   ├── schema/
│   └── supabase/
│
├── docs/
│   └── PROJECT_SCOPE.md
│
├── tests/
│
├── requirements.txt
├── requirements-render.txt
└── README.md
```

---

# Frontend Structure

The dashboard is composed of dedicated components including:

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

The main dashboard controller coordinates:

* authenticated data loading
* search results
* resume state
* opportunity state
* analytics
* UI refreshes after mutations

---

# Error Handling and Loading States

Network-dependent functionality exposes visible loading states rather than appearing unresponsive.

This is particularly important because the free Render backend can enter an idle state and require additional time for the first request after inactivity.

The user does not need to manually restart or redeploy the service.

CareerCompass displays loading feedback while the backend wakes and processes the request.

---

# Deployment Behaviour

## Vercel

The frontend remains deployed continuously.

A user's browser does not depend on:

* the developer's laptop
* VS Code
* a local terminal
* an open Vercel dashboard

---

## Render

The backend remains deployed but the free Render service may sleep after inactivity.

When a new request arrives:

```text
User request
     ↓
Render service wakes
     ↓
FastAPI starts
     ↓
Request completes
```

No manual redeployment is required.

---

## Supabase

Supabase independently hosts:

* authentication
* PostgreSQL database
* private resume storage

---

# Production Validation

The deployed CareerCompass application has been smoke-tested across its major workflows.

Validated production flows include:

```text
Guest dashboard
✓

Account creation
✓

Login
✓

Dark-mode authentication UI
✓

User isolation
✓

Resume upload
✓

Resume replacement
✓

Resume persistence after refresh
✓

Manual job URL import
✓

Manual resume comparison
✓

Save manual role to applications
✓

Immediate application-list refresh
✓

Application stage updates
✓

Application notes/events
✓

Application priority
✓

Application persistence
✓

Career Insights
✓

Live provider search
✓
```

---

# Search Quota

Provider searches are intentionally quota-controlled.

This prevents uncontrolled use of external provider APIs and makes search consumption visible to users.

Manual job URL imports do not consume provider-search quota.

---

# Data and Analytics Skills Demonstrated

Although CareerCompass is a full-stack application, much of its core functionality is built around data-analysis problems.

The project demonstrates:

## Python

Used for:

* data processing
* backend services
* text transformation
* requirement extraction
* matching
* aggregation
* analytics

---

## SQL

Used for:

* relational data modelling
* joins
* aggregation
* filtering
* profile ownership
* opportunity tracking
* requirement relationships
* concept mapping
* analytics queries

---

## Data Cleaning

CareerCompass processes heterogeneous job data from different sources.

Cleaning tasks include:

* title normalisation
* company normalisation
* description cleanup
* duplicate handling
* concept normalisation
* alias handling

---

## Data Transformation

Unstructured text is converted into structured information such as:

```text
raw job description
        ↓
requirements
        ↓
logical groups
        ↓
atomic concepts
        ↓
profile comparisons
```

---

## Data Quality Assessment

CareerCompass distinguishes jobs with sufficiently rich descriptions from listings that do not contain enough information for reliable assessment.

This prevents incomplete records from being interpreted as if they were complete.

---

## Data Integration

CareerCompass combines data originating from:

* multiple job providers
* public job pages
* uploaded resume documents
* authenticated user profiles
* application histories

into a unified relational model.

---

## Text Analytics

The project uses:

* token-based techniques
* normalisation
* TF-IDF
* cosine similarity
* fuzzy matching
* semantic embeddings
* rule-based extraction

to work with unstructured text.

---

## Feature and Taxonomy Design

Job requirements and resume evidence are transformed into a reusable concept vocabulary.

This required decisions around:

* concept granularity
* synonyms
* equivalent terminology
* candidate relationships
* evidence thresholds
* false-positive prevention

---

## Aggregation

Career Insights aggregates individual job requirements across a collection of opportunities to expose broader trends.

This transforms row-level job data into strategic user-level insight.

---

## Analytical Interpretation

CareerCompass separates several quantities that could otherwise be misleading if combined:

```text
Relevance
Fit
Eligibility
Data quality
```

The system treats them as distinct analytical dimensions rather than creating a single arbitrary hiring score.

---

## Data Visualisation and Communication

The frontend translates structured analysis into user-facing interfaces for:

* search relevance
* requirement comparison
* application pipelines
* recurring skill gaps
* application status
* upcoming events

This required converting backend data into information that can be interpreted quickly by users.

---

# Software Engineering Skills Demonstrated

CareerCompass also required:

* REST API design
* backend architecture
* frontend architecture
* authentication
* JWT handling
* secure environment configuration
* relational database design
* schema migrations
* private file storage
* multi-user ownership
* state management
* asynchronous UI design
* deployment
* production debugging
* Git/GitHub workflow
* cloud configuration
* CORS configuration

---

# Example CareerCompass Analysis

Suppose a listing contains:

```text
Requirements

- Strong SQL skills
- Experience with Python
- Experience with Power BI or Tableau
- Strong stakeholder communication
```

A user's resume contains:

```text
Technical Skills:
Python, SQL, Tableau

Experience:
Presented analysis to cross-functional stakeholders
```

CareerCompass may represent this conceptually as:

```text
SQL
→ Supported by your resume

Python
→ Supported by your resume

Power BI OR Tableau
→ Supported by Tableau

Stakeholder communication
→ Supported by experience evidence
```

If Power BI and Tableau were both absent:

```text
Power BI OR Tableau
→ Not shown on your resume
```

CareerCompass does not infer that the candidate cannot use those tools.

It only reports what the current resume demonstrates.

---

# Why Not Predict Hiring Probability?

Hiring depends on many variables CareerCompass cannot reliably observe, including:

* applicant competition
* recruiter preferences
* interview performance
* referral strength
* internal candidates
* headcount changes
* role urgency
* employer screening systems
* subjective assessment

Presenting a precise probability would therefore imply a level of certainty the available data cannot support.

CareerCompass instead focuses on observable evidence.

---

# Limitations

CareerCompass currently has several known limitations.

## Production Semantic Matching

The deployed free backend uses lightweight mode because the full embedding stack exceeds its memory allocation.

---

## Public Job Page Variability

Job websites differ considerably in:

* HTML structure
* client-side rendering
* anti-bot protection
* structured metadata
* description completeness

Some manual URLs may therefore be impossible to extract reliably.

---

## Requirement Extraction

Requirement extraction is heuristic.

Ambiguous job descriptions can still produce:

* incomplete requirements
* overly broad concepts
* candidate matches requiring review

---

## Cardinality

Complex conditions such as:

```text
At least 2 of the following 5 technologies
```

are not yet modelled fully.

---

## Resume Evidence

CareerCompass can only analyse evidence contained in the uploaded resume.

It cannot know skills or experiences the user has not documented.

---

## Hiring Outcomes

CareerCompass does not predict:

* ATS acceptance
* interview probability
* offer probability
* recruiter decisions

---

## Provider Coverage

Job discovery depends on the configured providers and therefore cannot guarantee complete coverage of every available job.

Manual URL import exists partly to address this limitation.

---

# Future Development

Potential future improvements include:

## Matching

* richer semantic matching in production
* improved concept disambiguation
* more sophisticated evidence attribution
* requirement-cardinality support

---

## Search

* additional job providers
* better company-level filtering
* improved deduplication
* more search filters
* search history

---

## Resume Intelligence

* guided resume tailoring
* section-level recommendations
* achievement-quality analysis
* role-specific resume versions

---

## Career Insights

* requirement trends by occupation
* skill-demand breakdowns
* application conversion analytics
* time-to-stage metrics
* historical application performance

---

## Application Management

* automated reminders
* scheduled follow-ups
* interview preparation links
* calendar integration
* deadline notifications

---

## Production Infrastructure

* stronger monitoring
* structured logging
* error tracking
* higher-memory backend hosting
* full production semantic model
* custom domain

---

# Project Status

CareerCompass is currently deployed and supports its intended core workflow:

```text
Account creation
      ↓
Job discovery
      ↓
Job requirement extraction
      ↓
Resume comparison
      ↓
Opportunity saving
      ↓
Application management
      ↓
Career Insights
      ↓
Resume improvement
```

The application has progressed from a local data-processing prototype into a multi-user deployed web application with authenticated data ownership, private document storage, job intelligence, resume analysis, application tracking and production infrastructure.

---

# Summary

CareerCompass combines:

```text
Job Discovery
+
Data Cleaning
+
Text Processing
+
Requirement Extraction
+
Resume Evidence Mapping
+
Similarity Analysis
+
Application Tracking
+
Career Analytics
```

into one integrated workflow.

The central idea is simple:

> Help users understand not only which opportunities are relevant, but also what those opportunities require, what their resume currently demonstrates, and what patterns emerge across the jobs they want.

```
```
