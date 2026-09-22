# CareerCompass

CareerCompass is a job-search, resume intelligence, and application management platform designed to help job seekers improve their chances of getting past early resume screening.

Its main feature is a transparent resume-to-job comparison system. CareerCompass reads a job description, extracts what the employer appears to be looking for, compares those requirements against the user's current resume, and explains which requirements are supported, which are not currently shown, and which still need review.

Beyond resume screening, CareerCompass also helps users discover or import jobs, track applications, manage hiring-stage events, review eligibility signals, and identify recurring skill gaps across the roles they are interested in.


---

## Why CareerCompass?

Job seekers increasingly face two connected challenges:

1. **Finding relevant opportunities**
2. **Getting past initial resume screening**, especially as employers increasingly use AI-assisted and automated tools to filter and prioritise applications before human review

CareerCompass is designed to support both:

```text
Discover Relevant Roles
        ↓
Understand Requirements
        ↓
Compare Against Resume
        ↓
Identify Missing or Weakly Shown Evidence
        ↓
Improve the Application
        ↓
Apply
        ↓
Track Progress
```

Its primary goal is to help job seekers find suitable opportunities while making early resume screening less opaque, so they can better understand what employers appear to be looking for and whether their current resume demonstrates those requirements clearly.

## Core Product Idea

CareerCompass deliberately separates signals that are often incorrectly combined into one vague "match score".

### Search Relevance

How closely a job matches the role, keywords, location, or other search criteria entered by the user.

### Resume Comparison

Whether CareerCompass can find supporting evidence in the user's current resume for requirements extracted from the job description.

### Eligibility

Whether known eligibility-related conditions appear to be satisfied based on available profile information.

### Application Progress

Where the user currently is in the hiring process.

These signals answer different questions and should not be interpreted as hiring probabilities.

---

## End-to-End Workflow

```text
Create Account
      ↓
Upload Resume
      ↓
Search for Jobs
or Import a Job URL
      ↓
Normalise Job Data
      ↓
Extract Job Requirements
      ↓
Map Requirements to Concepts
      ↓
Compare Requirements with Resume
      ↓
Review:
Supported / Not Shown / Needs Review
      ↓
Save to My Applications
      ↓
Track Application Progress
      ↓
Record OA / Interview / Follow-Up / Offer
      ↓
Review Career Insights
      ↓
Improve Future Applications
```

---

# Main Features

## 1. Authentication and User Accounts

CareerCompass supports authenticated user accounts.

Each user receives their own CareerCompass profile, and user-owned information is scoped to the authenticated account.

The platform follows the structure:

```text
Authentication
      ↓
User Account
      ↓
User Profile
      ↓
Current Resume
      ↓
Applications
```

Profile ownership is determined server-side rather than trusting profile identifiers sent by the browser.

---

## 2. Job Search

Users can search for job opportunities through supported job-data providers.

CareerCompass collects listings from multiple sources and normalises them into a common job format.

Normalised information can include:

* job title
* company
* location
* employment type
* posting URL
* posting date
* closing date
* salary text
* job description
* requirements
* source
* source job identifier

Search results are saved automatically so users can return to them without repeating the same search.

---

## 3. Search Quota Protection

CareerCompass includes per-user search quota controls.

The current free-account workflow limits users to two provider searches while preserving previously returned results.

Manual URL imports are handled separately and do not consume a provider search.

---

## 4. Manual Job Import

Users are not limited to jobs returned through CareerCompass search.

If a user already has a specific opportunity in mind, they can paste a public job-listing URL into CareerCompass.

The platform can attempt to:

1. read the listing
2. extract job information
3. identify the job description
4. extract job requirements
5. normalise requirement concepts
6. add the role to CareerCompass
7. compare the role against the user's resume
8. save the role to My Applications

CareerCompass supports generic public job pages and structured job-platform sources where available, including Lever listings.

If a page cannot be read automatically, the job description can be pasted manually.

---

## 5. Job Data Quality Checks

Not every job listing contains enough information for a meaningful comparison.

CareerCompass performs description-quality checks before running deeper analysis.

Listings with insufficient information can be flagged rather than producing misleading resume comparisons.

---

# Requirement Intelligence

## 6. Requirement Extraction

CareerCompass extracts meaningful requirements from job descriptions.

Examples include:

* skills
* tools
* programming languages
* domain knowledge
* education
* work experience
* certifications
* licences
* professional registrations
* security-clearance requirements
* physical requirements
* other role-specific conditions

The extracted requirements are stored separately from the original job description so they can be analysed individually.

---

## 7. Requirement Concept Normalisation

Job descriptions frequently express the same concept in different ways.

CareerCompass maps requirement text into reusable concepts.

For example:

```text
Proficiency in SQL is required
```

can be normalised to:

```text
SQL
```

with a normalised concept key such as:

```text
sql
```

This helps reduce false mismatches caused by wording or sentence structure.

CareerCompass supports:

* direct lexical matching
* normalised aliases
* curated equivalent terms
* spelling variants
* semantic candidate matches
* tool-name variations
* shared requirement concepts

---

## 8. Logical Requirement Groups

Some job requirements contain multiple skills or alternatives.

For example:

```text
Experience with Python and SQL
```

or:

```text
Experience with Python, R, or MATLAB
```

CareerCompass supports logical requirement structures including:

```text
ALL_OF
```

and:

```text
ANY_OF
```

This allows comparisons to better reflect how a requirement is written instead of treating every extracted keyword independently.

Open-ended groups can also be marked for review when the system should not make an overly strong conclusion.

---

# Resume Intelligence

## 9. Single Current Resume

CareerCompass intentionally supports one current resume per user.

This prevents evidence from multiple resume versions from being combined into a misleading profile.

The model is:

```text
User
 ↓
One Current Resume
 ↓
Claims + Evidence
 ↓
Job Comparisons
```

If the user uploads another resume, the new resume replaces the previous one.

---

## 10. Safe Resume Replacement

CareerCompass validates and processes a replacement resume before removing the previous version.

The intended replacement flow is:

```text
New Resume
    ↓
Validate File
    ↓
Extract Text
    ↓
Extract Sections
    ↓
Extract Claims and Evidence
    ↓
Upload New Private File
    ↓
Replace Database Resume
    ↓
Remove Old Resume-Derived Data
    ↓
Rebuild Profile Concept Mapping
    ↓
Refresh Comparison State
    ↓
Remove Previous Private File
```

This reduces the risk of a failed upload leaving the user without a usable resume.

---

## 11. Resume Parsing

Supported resume formats include:

* PDF
* DOCX
* TXT

CareerCompass extracts textual content and separates the resume into useful sections such as:

* Skills
* Experience
* Projects
* Education
* Certifications
* Languages
* Licences
* Awards
* Volunteering

---

## 12. Resume Claims and Evidence

CareerCompass distinguishes between direct claims and supporting evidence.

### Claims

Claims are usually short explicit statements such as:

```text
Python
SQL
Power BI
English
```

### Evidence

Evidence is longer resume content demonstrating how skills or experience were applied.

For example:

```text
Built an automated reporting dashboard using Power BI and SQL.
```

or:

```text
Developed a Python pipeline to clean and analyse transaction data.
```

This allows CareerCompass to distinguish between merely mentioning a skill and demonstrating it through experience or projects.

---

## 13. Profile Concept Mapping

Resume claims and evidence are mapped against the shared CareerCompass requirement vocabulary.

Matching can include:

* direct lexical matches
* aliases
* spelling variants
* curated candidate relationships
* semantic similarity

CareerCompass distinguishes high-confidence matches from weaker candidates instead of treating every semantic similarity as confirmed evidence.

---

# Resume Screening Support

## 14. Resume Comparison

CareerCompass compares extracted job requirements against the user's current resume.

Requirements are presented using understandable statuses.

### Supported by your resume

CareerCompass found sufficiently strong supporting evidence in the current resume.

### Not shown on your resume

CareerCompass did not find sufficient supporting evidence in the current resume.

This does **not** mean the user does not possess the skill.

It only means the current resume does not clearly demonstrate it.

### Needs review

CareerCompass found something potentially relevant, but the evidence is not strong enough for an automatic conclusion.

The goal is to help users identify where resume tailoring may be useful without inventing qualifications they do not have.

---

## 15. Resume Comparison for Saved Applications

Resume comparison is available directly from My Applications.

A user can reopen the comparison for any tracked application.

The comparison is refreshed when opened so it reflects the user's current CareerCompass resume rather than relying only on an old snapshot.

---

## 16. Search Match vs Resume Match

CareerCompass deliberately avoids treating search relevance as resume fit.

For example:

```text
Search Match: 91%
```

means that the job strongly matches the user's search terms.

It does **not** mean that the user's resume satisfies 91% of the employer's requirements.

Resume evidence is analysed separately.

---

# Eligibility

## 17. Eligibility Extraction

CareerCompass can identify requirements more closely related to candidate eligibility.

Examples include:

* education requirements
* years of experience
* licences
* certifications
* professional registrations
* other explicit eligibility conditions

---

## 18. Candidate Eligibility Facts

CareerCompass can extract relevant profile facts and compare them against job eligibility conditions.

Eligibility is intentionally kept separate from general skill matching.

---

# Application Management

## 19. My Applications

Users can save jobs into an application pipeline.

Saved jobs can come from:

* CareerCompass provider searches
* manually imported job URLs

---

## 20. Application Pipeline

Applications can move through stages such as:

```text
To Apply
Applied
Online Assessment
Interview
Offer
Closed
```

Internally, CareerCompass can maintain more detailed statuses including:

```text
discovered
saved
to_apply
applied
oa
interview
offer
rejected
withdrawn
closed
```

---

## 21. Application Details

Users can maintain information such as:

* priority
* application date
* application URL
* application method
* referral status
* cover-letter status
* notes
* current stage
* follow-up information

---

## 22. Application Timeline

CareerCompass supports events associated with an opportunity.

Examples include:

* application submitted
* status changed
* deadline
* online assessment
* interview
* follow-up
* offer
* rejection
* withdrawal
* note
* other events

This allows CareerCompass to function as more than a simple job bookmark list.

---

## 23. Smart Application Management

Tracked applications can include information used for sorting and prioritisation, such as:

* next event
* next event date
* priority
* application stage
* deadlines

The aim is to help users understand what requires attention next.

---

# Career Insights

## 24. Skill Gap Intelligence

CareerCompass analyses recurring requirement gaps across roles.

Instead of viewing each job independently, users can identify requirements that repeatedly appear in opportunities they are interested in.

For example:

```text
SQL appears in 8 target roles
Power BI appears in 5 target roles
Cloud experience appears in 4 target roles
```

This can help users decide what skills, tools, or experiences may be worth strengthening over time.

---

## 25. Job-Specific vs Recurring Insights

CareerCompass distinguishes between:

### Job-specific gaps

Useful when preparing for one particular application.

### Recurring gaps

Useful for longer-term career development.

This creates two levels of insight:

```text
Tactical:
"What should I address for this job?"

Strategic:
"What keeps appearing across the jobs I want?"
```

---

# User Interface

## 26. Main Workspace

CareerCompass is organised into four primary areas.

### Job Matches

Discover and review job opportunities.

### My Applications

Manage saved opportunities and track hiring progress.

### Career Insights

Review recurring requirements and gaps.

### My Profile

Manage the user's current resume and profile information.

---

## 27. Built-In Help Guide

CareerCompass includes an in-product **Need help?** guide.

The guide explains:

* how to upload a resume
* how to search for jobs
* how to import a job URL
* how resume comparisons work
* what comparison statuses mean
* how to track applications
* how Career Insights works
* the difference between search relevance, resume comparison, and eligibility

---

# Data and Privacy

CareerCompass stores personal resume data privately.

The application uses:

* authenticated user accounts
* user-scoped profiles
* private resume storage
* server-side ownership validation
* Supabase authentication
* PostgreSQL
* Supabase Storage
* row-level security where applicable

Resume files are stored in user-specific private storage paths.

Sensitive credentials and provider API keys remain server-side.

---

# Architecture

```text
                       ┌─────────────────┐
                       │     Next.js     │
                       │     Frontend    │
                       └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │     FastAPI     │
                       │      API        │
                       └────────┬────────┘
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
             ▼                  ▼                  ▼
      ┌────────────┐    ┌───────────────┐   ┌──────────────┐
      │ PostgreSQL │    │ Supabase Auth │   │   Storage    │
      └────────────┘    └───────────────┘   └──────────────┘
             │
             ▼
      ┌─────────────────┐
      │ Job Collection  │
      │ + Normalisation │
      └────────┬────────┘
               ▼
      ┌─────────────────┐
      │ Requirement     │
      │ Extraction      │
      └────────┬────────┘
               ▼
      ┌─────────────────┐
      │ Concept Mapping │
      └────────┬────────┘
               │
               ├───────────────┐
               ▼               ▼
      ┌─────────────────┐  ┌─────────────────┐
      │ Resume Evidence │  │ Eligibility     │
      │ Matching        │  │ Assessment      │
      └────────┬────────┘  └─────────────────┘
               ▼
      ┌─────────────────┐
      │ Applications +  │
      │ Career Insights │
      └─────────────────┘
```

---

# Technology Stack

## Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS

## Backend

* Python
* FastAPI
* SQLAlchemy

## Database and Authentication

* PostgreSQL
* Supabase Auth
* Supabase Storage
* Supabase Row-Level Security

## NLP and Matching

* rule-based extraction
* lexical concept matching
* alias matching
* sentence-transformers
* semantic similarity
* logical requirement groups

## Job Collection

The job collection architecture supports multiple sources.

Current integrations include:

* SerpAPI / Google Jobs
* Jooble
* direct public job URLs
* structured job-platform endpoints where supported

## Development and Deployment

* GitHub
* Vercel planned for frontend hosting
* production FastAPI hosting
* Supabase cloud services

---

# Repository Structure

```text
CareerLens/
│
├── api/
│   ├── routes/
│   ├── auth.py
│   ├── profile.py
│   └── index.py
│
├── src/
│   ├── cleaning/
│   ├── collection/
│   ├── eligibility/
│   ├── extraction/
│   ├── matching/
│   ├── services/
│   ├── taxonomy/
│   └── user_profile/
│
├── sql/
│   ├── schema/
│   └── supabase/
│
├── frontend/
│   └── src/
│       └── app/
│           └── dashboard/
│
├── tests/
├── docs/
└── README.md
```

---

# Local Development

## Backend

From the repository root:

```bash
cd CareerLens

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

uvicorn api.index:app --reload
```

The backend runs locally at:

```text
http://127.0.0.1:8000
```

FastAPI documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

## Frontend

```bash
cd frontend

npm install
npm run dev
```

The frontend normally runs at:

```text
http://localhost:3000
```

---

# Environment Variables

Local secrets should never be committed.

Backend configuration includes variables such as:

```text
SUPABASE_URL
SUPABASE_PUBLISHABLE_KEY
SUPABASE_DATABASE_URL
```

Job-provider credentials should also remain server-side.

Frontend public configuration may include:

```text
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
NEXT_PUBLIC_API_URL
```

Use local `.env` and `.env.local` files and keep them outside Git.

---

# Database Migrations

Schema migrations are stored under:

```text
sql/schema/
```

They should be applied in numerical order.

The project contains migrations covering areas including:

* core jobs and companies
* search tracking
* job quality flags
* requirement extraction
* requirement concepts
* user profiles
* resume storage
* authentication ownership
* application tracking
* requirement logic
* manual job imports
* single-resume enforcement

---

# Development Principles

## Explain Rather Than Over-Score

Where possible, CareerCompass shows requirement-level reasoning and evidence instead of reducing everything to one unexplained score.

## Do Not Invent Qualifications

If resume evidence is uncertain, CareerCompass should mark the requirement for review rather than automatically claiming that the user possesses the skill.

## Keep Different Signals Separate

Search relevance, resume evidence, eligibility, and application progress are distinct concepts.

## Preserve User Privacy

Resume files and user-owned application data should remain isolated between accounts.

## Support Real Job-Search Workflows

CareerCompass is designed around what happens both before and after an application, not only job discovery.

---

# Current Product Status

The core CareerCompass workflow has been implemented locally, including:

* authentication
* user profiles
* one current resume per user
* safe resume replacement
* resume parsing
* resume claim and evidence extraction
* profile concept mapping
* multi-source job search
* search quotas
* job normalisation
* search relevance
* job-description quality checks
* requirement extraction
* requirement concept normalisation
* logical requirement groups
* manual job URL import
* resume comparison
* eligibility analysis
* saved opportunities
* application pipeline
* application events
* recurring skill-gap insights
* in-product help

The next major milestone is production deployment and production hardening.

---

# Planned Improvements

## Deployment and Production Hardening

Planned work includes:

* production frontend deployment
* production FastAPI deployment
* production environment configuration
* production CORS configuration
* logging
* monitoring
* improved error handling
* deployment smoke tests
* final security checks

---

## Resume Tailoring Assistance

Future versions of CareerCompass could use identified requirement gaps to help users improve how genuine experience is presented on their resume.

Any suggestions should remain grounded in the user's actual background rather than inventing qualifications or experiences.

---

## Better Requirement Understanding

Potential improvements include:

* richer requirement grouping
* cardinality requirements
* improved equivalence detection
* stronger role-specific taxonomies
* improved confidence handling

---

## Application Analytics

Potential analytics include:

* application conversion rates
* online assessment conversion
* interview conversion
* offer conversion
* response time
* source effectiveness
* recurring rejection stages

---

## Additional Job Sources

The collection architecture can support additional job providers and career sites where appropriate.

---

## Broader Career Intelligence

CareerCompass can eventually connect job requirements, application outcomes, and recurring gaps to provide longer-term career-development insights.

---

# Limitations

CareerCompass performs automated extraction and comparison and can make mistakes.

A missing match does not necessarily mean the user lacks a skill.

A detected match does not guarantee that an employer will consider the evidence sufficient.

Job descriptions may also be incomplete, ambiguous, or inaccurate.

CareerCompass should therefore be used as a decision-support tool rather than an authoritative hiring assessment.

---

# Security Notes

Never commit:

```text
.env
.env.local
database passwords
Supabase service credentials
provider API keys
access tokens
private resume files
private user data
```

Recommended `.gitignore` entries include:

```gitignore
.env
.env.*
!.env.example

.venv/
node_modules/
.next/

__pycache__/
*.pyc

data/private/
```

---

# Project Goal

CareerCompass aims to help job seekers make stronger, better-informed applications.

The central question is:

> Before I submit this application, does my resume clearly demonstrate what this employer appears to be looking for?

CareerCompass attempts to answer that question transparently while also helping users discover opportunities, organise applications, track hiring progress, and understand recurring areas for improvement.
