# CareerLens Project Scope

## 1. Project Overview

CareerLens is a personal career intelligence and application management system for students and early-career candidates.

Its purpose is to transform real-world job-market data and personal application history into transparent, actionable career information.

The system is designed around the following feedback loop:

**Job Market → Discover → Evaluate → Identify Gaps → Develop Evidence → Apply → Track → Analyse Outcomes → Improve**

CareerLens should be treated as a career intelligence system rather than simply a job-market dashboard.

---

## 2. Initial Target User

The initial user is a student or early-career candidate searching for analytics-related internships and junior positions.

CareerLens V1 will initially focus on Singapore opportunities.

---

## 3. Initial Target Roles

The initial role taxonomy will focus on:

* Data Analyst
* Business Analyst
* BI Analyst
* Product Analyst
* Operations Analyst
* Data / Analytics Intern
* Related entry-level analytics roles

Additional roles can be introduced later if sufficient relevant data is available.

---

## 4. Core Research Questions

### Job Market

CareerLens should investigate:

* What technical skills are most frequently requested?
* What non-technical skills are most frequently requested?
* How do requirements differ across analytics roles?
* How do internship requirements differ from graduate or junior-role requirements?
* Which skills commonly appear together?
* Which tools and technologies are genuinely requested by employers?
* How do employers describe similar skills using different terminology?
* How do requirements differ across industries and company types?
* How does observed demand change over time once sufficient historical data exists?

### Student and Job Comparison

CareerLens should investigate:

* Which job requirements can the student demonstrate using existing evidence?
* Which requirements have only partial evidence?
* Which requirements currently have no supporting evidence?
* Which skill gaps are common across the student's target jobs?
* Which potential development activities could address multiple evidence gaps?

### Personal Application Analytics

Once sufficient personal application data exists, CareerLens should investigate:

* Which roles generate the most responses?
* Which roles generate the most interviews?
* Which application sources are associated with different outcomes?
* How long do companies typically take to respond?
* At which stage do applications most commonly stop progressing?
* Are higher levels of demonstrated requirement coverage associated with different outcomes?
* How have different CV versions performed descriptively?

CareerLens will distinguish association from causation and will not make unsupported causal claims.

---

## 5. CareerLens V1 Features

### Job Market Dataset

Store structured information about real job postings, including:

* company;
* job title;
* canonical role;
* location;
* industry;
* employment type;
* seniority;
* salary where available;
* job description;
* requirements;
* education requirements;
* experience requirements;
* date posted;
* source;
* application URL;
* closing date where available;
* date captured.

Raw source information should be preserved where possible.

### Role Taxonomy

Job titles should be mapped from raw employer terminology into consistent role categories while retaining the original title.

### Skill Taxonomy

CareerLens will define canonical skills and aliases.

For example:

SQL may include terminology such as:

* SQL;
* SQL querying;
* relational database querying.

The taxonomy should avoid incorrectly treating related but distinct technologies as identical.

### Skill Extraction

CareerLens will initially implement a transparent rule-based extraction baseline.

More advanced NLP, embedding-based, LLM-assisted, or hybrid extraction methods may subsequently be evaluated against a manually labelled validation dataset.

Extraction performance should be measured rather than assumed.

### Student Evidence Profile

CareerLens will distinguish between:

* a skill the student claims to possess; and
* evidence demonstrating that skill.

Evidence may include:

* projects;
* work experience;
* coursework;
* certifications;
* competitions;
* other relevant activities.

### Requirement Mapping

For a saved job, CareerLens will compare identified requirements against the student's evidence.

The output should explain which requirements have:

* strong evidence;
* partial evidence;
* limited evidence;
* no evidence.

CareerLens will not present an unsupported hiring probability or claim that it can predict whether the student will receive an offer.

### Opportunity and Application Tracking

Opportunities should be tracked through stages such as:

**Discovered → Saved → To Apply → Applied → Online Assessment → Interview → Offer / Rejected / Withdrawn**

Application events should be recorded historically rather than simply overwriting the current status.

### Application Analytics

Once sufficient application history exists, CareerLens should provide descriptive analysis of:

* application funnel;
* response rate;
* interview rate;
* response times;
* role;
* company;
* application source;
* resume version;
* skill coverage;
* rejection stage.

Sample sizes should always be considered when interpreting results.

---

## 6. Data Pipeline

The intended high-level pipeline is:

**Data Source → Raw Data → Cleaning / Standardisation → PostgreSQL → Analysis / NLP → Analytical Views → BI / Application Layer**

Raw data should not be overwritten during transformation.

---

## 7. Data Quality Considerations

CareerLens should explicitly consider:

* duplicate postings;
* reposted jobs;
* missing fields;
* inconsistent company names;
* inconsistent job titles;
* inconsistent locations;
* terminology differences;
* expired postings;
* changed postings;
* salary inconsistencies;
* source-specific biases;
* sampling bias;
* geographic bias.

Data cleaning decisions should be documented and reproducible.

---

## 8. Methodological Principles

CareerLens should:

1. prefer transparent and interpretable methods where possible;
2. establish simple baselines before introducing complex models;
3. evaluate NLP and LLM outputs using labelled data;
4. distinguish observation from recommendation;
5. distinguish correlation from causation;
6. report sample sizes when analysing personal outcomes;
7. preserve raw data for reproducibility;
8. avoid misleading hiring or success probabilities.

---

## 9. Privacy and Ethics

CareerLens should comply with applicable data-source terms, API requirements, robots.txt requirements, and relevant laws.

Personal application information should not be publicly exposed in the GitHub repository.

Private data may include:

* personal CV information;
* application notes;
* interview details;
* recruiter information;
* personal application history.

Secrets and credentials must never be committed to GitHub.

---

## 10. Out of Scope for V1

CareerLens V1 will not prioritise:

* hiring probability prediction;
* automatic job applications;
* fully automated career advice;
* complex recommendation systems;
* demand forecasting without sufficient historical observations;
* multi-user authentication;
* production SaaS infrastructure;
* large-scale cloud or distributed computing.

These may be reconsidered only where they solve a demonstrated problem.

---

## 11. V1 Success Criteria

CareerLens V1 should demonstrate an end-to-end analytical workflow:

**Problem Definition → Data Collection → Data Cleaning → Data Modelling → SQL → Analysis → NLP → BI → Product/Application Layer**

A successful MVP should include:

* a reproducible dataset of real analytics job postings;
* a documented relational database;
* cleaned and standardised job data;
* a functioning role taxonomy;
* a functioning skill taxonomy;
* an evaluated skill-extraction method;
* meaningful job-market analysis;
* an evidence-based student profile;
* transparent job-requirement comparison;
* structured application tracking;
* personal application analytics when sufficient data exists;
* a stakeholder-oriented BI dashboard;
* clear documentation of assumptions and limitations.

The priority is a smaller, well-designed and genuinely working system rather than a large collection of unfinished features.
