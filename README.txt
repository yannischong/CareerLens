CareerLens UI/UX round 2

Changed files:
- frontend/src/app/dashboard/dashboard-client.tsx
- frontend/src/app/dashboard/career-compass-header.tsx
- frontend/src/app/dashboard/manual-job-import.tsx

Changes:
1. Restores startup loading estimate: Estimated time: 10–20 seconds.
2. Job search is collapsed by default and opens when the (CLICK HERE) link is clicked.
3. Removes the manual-job-import/provider-search quota sentence.
4. Gives the primary job analyser a polished blue gradient + glass/bubble UI matching the search experience.
5. Search Another Role / lower search links automatically open the collapsed search panel before focusing it.

From the CareerLens repo root:
  unzip -o careerlens_uiux_round2_fix.zip -d .
  cd frontend
  npm run lint
  npm run build

Validation performed here:
- npm run lint: PASS (0 errors, 0 warnings)
- local sandbox build could not complete because Next.js attempted to download a Linux SWC package and outbound network is unavailable in the sandbox.
