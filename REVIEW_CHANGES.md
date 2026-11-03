# Revision 12 — independent test comparisons and Thread B integration

Based on c7223dd. Integrates Thread A (`3cf0e02`) and Thread B (`1220f38`). Retains all 308 sample tests, the existing storage key, one row per test, and the separate choose/save/approve/download steps.

1. Snapshot comparisons capture each test's own expected file row before changing any state. One mismatch cannot invalidate another test's expected values. Matching tests become Done and stay out of To review; the differing test returns to review. Multi-test browser checks exercise mismatches first, middle, and last, including Thread B's `b-mismatch-positions` unchanged. Older browser data affected by a comparison cascade is repaired without a reset.
2. A comparison mismatch says which test differs from the file and directs the reviewer to To review. It does not label the observed file “Do not import.” A changed choice or approval withdrawal still retires unconfirmed files with that warning. Confirmed receipts remain historical records.
3. Normal downloads say “Nothing has reached OLSD yet.” Only partly confirmed files use the longer wording and name the remaining tests.
4. Thread B's Add a note control for entry edits and single-card numbering are integrated without editing `choiceCards` or `entryEditor`. An additional keyboard-handler regression covers the sole card for a field without an Epic source. No Thread B check was changed.

Release validation: 498 browser checks passed, with no JavaScript errors. The measured save/single-download/32-name paths remain 2/5/7 clicks. See verification.json for the exact tested source commit, source/test hashes, date, and integration commits.

Posit Connect remains the intended production target. This published site is still the sample-data browser prototype.

---

# Revision 11 — draft notes and durable confirmations

Addresses the review at e1f02f2. The 308-test sample catalog, storage key, one-row-per-test workflow, and separate choose/save/approve/download actions are retained.

1. Notes typed since the last Save stay with the draft when a card is chosen or wording is corrected. A saved note is cleared only when its saved choice/wording changes and the note has not been deliberately edited since Save. The earlier saved reason remains separate and in History.
2. Decide later stores a snapshot of the earlier saved value before resetting the proposal to OLSD. Decide now accurately says Before setting this aside, you chose…, offers genuinely different saved wording as a card, and preserves custom wording in the text box. Older deferred records can recover this value from their saved change history.
3. A successful catalog observation creates an immutable confirmation receipt per test in each file. Later editing, approval withdrawal, or Epic changes do not retire already-confirmed rows or change their Done date. Partly confirmed files preserve those receipts while returning only unconfirmed tests for clean replacement files. Later comparisons are separate from the historical receipt. Startup also restores valid earlier confirmations that the previous prototype incorrectly retired.
4. Equal Epic and OLSD values use one Keep what is in the OLSD (matches Epic) card. Any genuinely different saved wording remains a separate option.
5. New workbook names use the screen's America/New_York local date/time, such as DEMO_OLSD_TSH_2026-11-03_1505.xlsx. A short numeric suffix appears only for a filename collision, including multiple files from one click. Long IDs remain internal. Original historical filenames are not rewritten. The outdated-file warning avoids claiming that the values differ, and comparison text says matches this file.

Browser cases cover requested items 1–4 and the smaller filename/copy changes. They include draft notes before card selection, wording corrections, explicit note reuse, deferred-value recovery, later editing/Epic changes after confirmation, partial confirmation, legacy receipt recovery, and equal-value cards. Earlier workflow regressions remain in the full suite; see verification.json for the exact tested commit, source/test hashes, and results.

Posit Connect remains the production target. This is still a browser-storage prototype with simulated source checks; shared persistence, authentication, real source integrations, and scheduled jobs remain production work.

Release validation: 415 browser checks passed, with no JavaScript errors. The measured save/single-download/32-name paths remain 2/5/7 clicks.
