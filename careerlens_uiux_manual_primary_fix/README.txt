CareerLens / CareerCompass UI/UX — Manual Job Analyser Primary Fix
====================================================================

Requested changes included
--------------------------
1. "Upload Resume" is added beside "Read Job Listing".
2. The manual job-listing analyser becomes the main/primary hero workflow.
3. "How to use CareerCompass" is rewritten around the new primary workflow.
4. The job-link analyser open/close button is removed; the analyser stays visible.
5. Job search is treated as the secondary opportunity-discovery flow and uses:
   "Looking for more opportunities? Search your desired role here (CLICK HERE)"

Affected files
--------------
frontend/src/app/dashboard/manual-job-import.tsx
frontend/src/app/dashboard/career-compass-header.tsx
frontend/src/app/dashboard/career-compass-help.tsx
frontend/src/app/dashboard/dashboard-client.tsx

How to apply
------------
1. Copy apply_uiux_fix.py into the ROOT of your CareerLens repository.
2. From the repository root:

   python3 apply_uiux_fix.py

3. Validate:

   cd frontend
   npm run lint
   npm run build

4. Review:

   git diff

Safety
------
The script checks every expected source block first and only writes the files
after all four components pass validation. If your local code has diverged from
the current main-branch structure, it stops instead of partially applying the fix.
