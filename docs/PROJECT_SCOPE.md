# CareerCompass Project Scope

## 1. Project Overview

CareerCompass is a career intelligence, resume-screening support, and application management platform for job seekers.

The project focuses on two connected problems:

1. **Finding relevant job opportunities**
2. **Improving a candidate's ability to get past initial resume screening**, particularly as employers increasingly use automated and AI-assisted screening tools before or alongside human review

CareerCompass is designed to support the job-search journey beyond simply returning job listings. It helps users understand what employers appear to be looking for, compare those requirements against evidence in their current resume, identify areas that are not clearly demonstrated, track applications, and review recurring patterns across the roles they are targeting.

The intended user journey is:

```text
Discover
   ↓
Understand
   ↓
Compare
   ↓
Improve
   ↓
Apply
   ↓
Track
   ↓
Analyse
```

CareerCompass is a decision-support system. It does not guarantee interviews, offers, or hiring outcomes.

---

## 2. Target Users

CareerCompass is intended for job seekers who want more structured support during the application process, including:

- students
- internship applicants
- graduate job seekers
- early-career candidates
- candidates changing roles or industries
- other users who want to understand how their resume aligns with job requirements

The system should not depend on a fixed occupation selected by the developer.

A user should be able to search for occupations such as:

- Data Analyst
- Software Engineer
- Human Resources Analyst
- Product Analyst
- Quantitative Analyst
- Marketing Analyst
- Operations Analyst
- or other occupations supplied at runtime

CareerCompass should therefore remain **occupation-agnostic** wherever possible.

---

## 3. Geographic Scope

The initial implementation and validation of CareerCompass focuses primarily on **Singapore job-market data**.

This is an implementation and validation boundary rather than an architectural restriction.

The underlying system should be designed so that additional countries, cities, and job markets can be supported without requiring a redesign of the core architecture.

---

# 4. Core Product Objectives

CareerCompass should help users answer the following questions:

### Job Discovery

> What relevant opportunities are currently available?

### Requirement Understanding

> What does this employer appear to be looking for?

### Resume Screening Readiness

> Does my current resume clearly demonstrate those requirements?

### Application Management

> Which roles have I saved or applied for, and what should I do next?

### Career Development

> Which requirements repeatedly appear across the roles I want?

These objectives form the basis of the platform.

---

# 5. Job Discovery

## 5.1 Runtime Search

CareerCompass should allow users to enter their target occupation and location at runtime.

The system should not require a separate hardcoded module for every occupation.

Search terms should be treated as user input and passed through the common CareerCompass job-search pipeline.

---

## 5.2 Multiple Job Sources

CareerCompass should support job collection from multiple providers.

The current architecture supports sources including:

- SerpAPI / Google Jobs
- Jooble
- manually imported public job URLs
- structured public job-platform endpoints where available

Additional providers may be added later.

Provider-specific responses should be converted into a common internal job representation.

---

## 5.3 Job Normalisation

CareerCompass should normalise provider data into a common schema.

Relevant fields may include:

- company
- raw company name
- job title
- canonical role
- location
- country
- employment type
- seniority
- salary text
- job description
- requirements
- education requirements
- experience requirements
- posting date
- closing date
- source
- source job ID
- application URL
- first-seen date
- last-seen date
- active/inactive status

The system should avoid building downstream logic around provider-specific response formats.

---

## 5.4 Search Relevance

CareerCompass should rank returned jobs according to how closely they match the user's search.

Search relevance must remain conceptually separate from resume suitability.

For example:

```text
Search Match: 90%
```

means the role is highly relevant to the user's search query.

It does **not** mean that the user's resume satisfies 90% of the employer's requirements.

---

## 5.5 Search Quota

CareerCompass currently supports a limited number of provider searches per authenticated user.

Search results should be saved so users do not need to repeatedly consume searches to access previously returned jobs.

Manual job imports should not consume the user's provider-search quota.

---

# 6. Manual Job Import

CareerCompass should allow a user to analyse a role even when it is not returned by the built-in search.

The user can provide a public job-listing URL.

The platform should attempt to:

1. validate the URL
2. retrieve the public listing
3. extract job metadata
4. extract the job description
5. identify requirements
6. normalise requirement concepts
7. store the role in CareerCompass
8. compare it against the user's current resume
9. optionally save it to My Applications

Where possible, CareerCompass may use structured public job-platform APIs.

If a listing cannot be retrieved automatically, the user should be able to paste the job description manually.

The URL reader must include protections against unsafe internal or private network access.

---

# 7. Job Data Quality

CareerCompass should not assume that every collected listing contains enough information for meaningful analysis.

Job descriptions should be assessed for data quality.

Examples of potential quality issues include:

- missing descriptions
- very short descriptions
- incomplete provider responses
- duplicate listings
- stale listings
- descriptions containing insufficient requirement information

Jobs with insufficient data should be flagged rather than producing an unjustifiably confident resume comparison.

---

# 8. Requirement Intelligence

## 8.1 Requirement Extraction

CareerCompass should identify meaningful requirements from job descriptions.

Requirement types may include:

- skills
- tools
- programming languages
- domain knowledge
- education
- experience
- certifications
- licences
- professional registrations
- security clearance
- physical requirements
- other role-specific conditions

The platform should not treat employer requirements as only a list of technical skills.

---

## 8.2 Requirement Levels

Where supported by the job description, CareerCompass should distinguish between:

- required
- preferred
- unknown / unspecified

A preferred requirement should not automatically be treated as a strict eligibility condition.

---

## 8.3 Requirement Concept Normalisation

Different job descriptions may refer to the same underlying requirement using different wording.

CareerCompass should map related expressions into reusable concepts.

For example:

```text
Proficiency in SQL is required
Experience with SQL
SQL querying
```

should be capable of mapping to a shared concept such as:

```text
SQL
```

Normalisation may use:

- deterministic text cleaning
- lexical matching
- aliases
- curated equivalences
- spelling variants
- semantic similarity

The system should prefer high-confidence deterministic matches where possible.

---

## 8.4 Logical Requirement Groups

CareerCompass should recognise when a requirement contains multiple conditions.

Examples:

```text
Python and SQL
```

may require an `ALL_OF` interpretation.

```text
Python, R, or MATLAB
```

may require an `ANY_OF` interpretation.

The system should support logical requirement groups rather than treating every extracted concept as an unrelated independent requirement.

Where a requirement is open-ended or ambiguous, CareerCompass should prefer a `needs_review` state rather than making an unsupported conclusion.

---

# 9. Resume Model

## 9.1 One Current Resume Per User

CareerCompass should support **one current resume per authenticated profile**.

Uploading a new resume replaces the previous resume.

This design prevents evidence from several resume versions from being combined into one artificially strong profile.

The intended model is:

```text
User Profile
      ↓
One Current Resume
      ↓
Claims + Evidence
      ↓
Job Comparisons
```

---

## 9.2 Supported Resume Types

CareerCompass currently supports:

- PDF
- DOCX
- TXT

Resume files should be validated before processing.

---

## 9.3 Private Resume Storage

Resume files contain personal information and should be treated as private user data.

Files should be stored in authenticated user-specific private storage.

A user must not be able to access another user's resume through the application.

Sensitive storage credentials must not be exposed to the frontend.

---

## 9.4 Safe Resume Replacement

When a user replaces their resume, CareerCompass should:

1. validate the new file
2. extract its text
3. extract sections, claims, and evidence
4. store the new private file
5. replace the existing database resume
6. remove old resume-derived claims and evidence
7. rebuild concept mappings
8. invalidate or refresh stale fit and eligibility results
9. remove the previous private resume file

The previous resume should not be removed before the replacement has been sufficiently validated to avoid unnecessary data loss from a failed upload.

---

# 10. Resume Profile Extraction

CareerCompass should extract structured information from the current resume.

Relevant sections may include:

- skills
- experience
- projects
- education
- certifications
- languages
- licences
- professional registrations
- awards
- volunteering

The platform should distinguish between **claims** and **evidence**.

---

## 10.1 Claims

Claims are direct assertions appearing in the resume.

Examples:

```text
SQL
Python
Power BI
English
```

A claim shows that the resume explicitly mentions a concept.

---

## 10.2 Evidence

Evidence represents resume content demonstrating experience or application of a concept.

Example:

```text
Built an automated reporting dashboard using SQL and Power BI.
```

Evidence is generally stronger than an isolated skill-list mention.

---

# 11. Profile Concept Mapping

CareerCompass should map resume claims and evidence to the same requirement-concept vocabulary used for job descriptions.

Matching methods may include:

- exact lexical matches
- aliases
- spelling variants
- curated equivalences
- semantic candidates

Matches should maintain a distinction between:

- confirmed evidence
- candidate evidence
- no evidence

Semantic similarity should not automatically be treated as proof that a user possesses a requirement.

---

# 12. Resume Screening Comparison

Resume comparison is the central CareerCompass feature.

For an assessable job, CareerCompass should compare job requirements against the current resume.

User-facing outcomes should include categories such as:

### Supported by your resume

CareerCompass found sufficiently strong supporting information.

### Not shown on your resume

CareerCompass did not find enough supporting information in the current resume.

This wording must not imply that the user definitely lacks the skill.

### Needs review

The system found potentially relevant information but cannot confidently determine whether the requirement is supported.

CareerCompass should explain comparison results at the requirement level rather than relying solely on an overall opaque score.

---

# 13. Eligibility Assessment

CareerCompass should treat eligibility separately from general resume fit.

Potential eligibility requirements include:

- education
- years of experience
- certifications
- licences
- professional registrations
- other explicit candidate conditions

Where sufficient profile information exists, CareerCompass may compare eligibility requirements against extracted user facts.

Eligibility results should be presented conservatively.

Absence of information should not automatically be interpreted as confirmed ineligibility.

---

# 14. Opportunity and Application Tracking

Users should be able to save jobs to **My Applications**.

Tracked jobs may originate from:

- provider searches
- manually imported job URLs

The opportunity pipeline should support stages such as:

```text
To Apply
Applied
Online Assessment
Interview
Offer
Closed
```

Underlying statuses may include:

- discovered
- saved
- to_apply
- applied
- oa
- interview
- offer
- rejected
- withdrawn
- closed

---

## 14.1 Application Information

CareerCompass may store application-related information including:

- application date
- application URL
- application method
- priority
- referral status
- cover-letter usage
- notes
- current status

---

## 14.2 Application Events

Users should be able to record timeline events including:

- deadline
- online assessment
- interview
- follow-up
- offer
- rejection
- withdrawal
- status change
- note
- other events

The application should use event dates and priorities to help users identify upcoming actions.

---

## 14.3 Resume Comparison from Applications

Every saved application should allow the user to reopen its resume comparison.

The comparison should use the user's **current resume**.

It should be refreshed when opened so that replacing the resume updates future comparisons.

---

# 15. Career Insights

CareerCompass should aggregate information across relevant jobs to identify recurring requirement patterns.

Examples include:

- requirements frequently appearing in target roles
- requirements repeatedly not shown in the current resume
- frequently supported skills
- requirements that repeatedly require manual review

The product should distinguish between:

### Tactical Insights

What should the user consider for one specific job?

### Strategic Insights

What requirements repeatedly appear across many target jobs?

This allows CareerCompass to support both application preparation and longer-term career development.

---

# 16. User Interface Scope

The core CareerCompass workspace should contain four major areas.

## Job Matches

Used to:

- review search results
- inspect job details
- see search relevance
- inspect extracted requirements
- save jobs

## My Applications

Used to:

- review tracked jobs
- update pipeline stages
- manage deadlines and events
- reopen job postings
- reopen resume comparisons

## Career Insights

Used to:

- review recurring requirements
- identify repeated gaps
- understand patterns across target roles

## My Profile

Used to:

- view the current resume
- upload or replace the resume
- review profile-related information

---

# 17. Help and Onboarding

CareerCompass should provide an in-product help guide.

The guide should explain:

- how to upload a resume
- how to search for a role
- how to import a job URL
- how to interpret search relevance
- how to interpret resume comparison
- how eligibility differs from resume fit
- how to track applications
- how Career Insights works

The product should avoid requiring the user to understand implementation-specific terminology.

---

# 18. Authentication and Ownership

CareerCompass is a multi-user system.

All personal data must be associated with the authenticated user's profile.

User ownership should be derived from authentication rather than trusted from browser-supplied IDs.

User-owned resources include:

- profile
- resume
- searches
- manually imported jobs
- tracked opportunities
- application information
- events

The system must prevent cross-account access to private resources.

---

# 19. Data and Security Boundaries

CareerCompass should:

- keep provider API keys server-side
- keep database credentials server-side
- keep private resume files out of Git
- prevent public access to private resume storage
- validate user ownership on protected API operations
- avoid exposing raw secrets in frontend code
- avoid committing `.env` files
- avoid storing private resumes in the repository

---

# 20. System Architecture

The current architecture consists of:

```text
Next.js / React / TypeScript
            ↓
         FastAPI
            ↓
     PostgreSQL / Supabase
            ↓
 ┌──────────┼───────────┐
 │          │           │
Auth     Storage     Job Data
 │                      │
 ▼                      ▼
Profile            Normalisation
 │                      │
Resume              Requirements
 │                      │
Claims/Evidence     Concepts
 └──────────┬───────────┘
            ▼
     Resume Comparison
            ↓
 Applications + Insights
```

Core technologies include:

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

### Backend

- Python
- FastAPI
- SQLAlchemy

### Data and Authentication

- PostgreSQL
- Supabase Auth
- Supabase private Storage
- row-level security where applicable

### Matching

- deterministic extraction
- lexical matching
- aliases
- sentence-transformers
- semantic candidate matching
- logical requirement groups

---

# 21. Current Implementation Scope

The current CareerCompass implementation includes:

- authenticated user accounts
- user-scoped profiles
- one current resume per user
- safe resume replacement
- resume parsing
- resume claim extraction
- resume evidence extraction
- profile concept mapping
- job search through multiple sources
- per-user search quotas
- saved search results
- job normalisation
- description quality checks
- search relevance ranking
- requirement extraction
- requirement concept normalisation
- logical requirement groups
- manual public job URL import
- manual job-description fallback
- resume comparison
- eligibility extraction and assessment
- opportunity saving
- application pipeline tracking
- application events
- deadline and next-event information
- recurring skill-gap analysis
- in-product help

The next major implementation milestone is production deployment and production hardening.

---

# 22. Out of Scope for the Current MVP

The following should not be treated as required for the current MVP.

## Hiring Probability

CareerCompass should not claim:

```text
You have an 83% chance of getting an interview.
```

unless a future version has appropriate validated outcome data and a defensible modelling methodology.

## Automated Candidate Decisions

CareerCompass is a tool for job seekers.

It is not intended to automatically accept, reject, rank, or screen candidates on behalf of employers.

## Inventing Resume Experience

CareerCompass may eventually suggest clearer ways to present genuine experience, but it should not fabricate:

- skills
- employment
- education
- projects
- certifications
- achievements

## Universal Job-Site Scraping

CareerCompass does not guarantee automatic extraction from every website.

Some job sites may block automated retrieval or require authentication.

Manual description entry remains an acceptable fallback.

## Complete Applicant Tracking System Replacement

CareerCompass tracks the user's own applications but is not intended to replace enterprise ATS software used by employers.

## Full International Coverage

Singapore is the initial validation market.

International expansion is possible but is not required for the current MVP.

---

# 23. Future Extensions

Potential post-MVP extensions include:

## Resume Tailoring Assistance

Provide grounded suggestions for improving how genuine experience is presented against a specific role.

Suggestions should be based on existing resume evidence and should not invent qualifications.

## Improved Requirement Modelling

Potential improvements include:

- cardinality requirements such as "2 of the following 5 skills"
- stronger entity and skill taxonomies
- better multi-sentence extraction
- richer semantic equivalence handling
- confidence calibration

## Application Analytics

Potential analytics include:

- application-to-OA conversion
- application-to-interview conversion
- interview-to-offer conversion
- source effectiveness
- response times
- recurring rejection stages
- outcomes by job category

Any conclusions about causation should be avoided unless supported by sufficient evidence.

## Additional Job Sources

Additional providers may be integrated without changing the common job model.

## Broader Career Intelligence

Future versions could connect:

```text
Job Requirements
      +
Resume Evidence
      +
Application Outcomes
      ↓
Long-Term Career Insights
```

---

# 24. Production Deployment Scope

The production deployment phase should include:

- GitHub source-control checkpoint
- production frontend hosting
- production FastAPI hosting
- production environment variables
- Supabase production configuration
- production CORS configuration
- database migration verification
- authentication smoke testing
- resume upload and replacement testing
- manual job import testing
- job-search testing
- application tracking testing
- user-isolation testing
- production logging and error handling

The platform should only be considered deployment-ready after these flows have been verified in the production environment.

---

# 25. Success Criteria

The CareerCompass MVP is successful if a user can:

1. create or access an authenticated account
2. upload one current resume
3. replace that resume safely
4. search for an occupation at runtime
5. receive and revisit relevant job listings
6. import a specific public job listing manually
7. understand the requirements extracted from a job
8. compare those requirements against their current resume
9. understand which requirements are supported, not shown, or need review
10. save jobs to My Applications
11. track application stages and important events
12. reopen resume comparisons from saved applications
13. review recurring requirement gaps across target roles
14. use the platform without accessing another user's private data

The project should achieve these goals without presenting unsupported hiring probabilities or pretending that automated matching can determine hiring outcomes.

---

# 26. Project Principle

The central CareerCompass question is:

> Before I submit this application, does my resume clearly demonstrate what this employer appears to be looking for?

CareerCompass should help the user answer that question transparently while also supporting relevant job discovery, application organisation, and longer-term career improvement.
