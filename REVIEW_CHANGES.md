# Revision 10 — deferral, retired files, and note provenance

Addresses the next-fixes review at 138948c. The 308-test sample catalog and existing browser-storage key are retained. The one-row-per-test worklist and separate choose/save/approve/download steps remain.

1. Decide later on a reopened choice restores its open Epic change, resets proposed content to OLSD, and saves the test under Set aside. Pending fields prevent approval, and Save withdraws an existing approval. Authored-only fields without an Epic difference have no Decide later action. Loading old browser data also recovers orphaned deferrals left by the earlier bug, preserving their reasons.
2. Each new Excel filename includes a UTC timestamp and unique download ID. Changing a saved choice/content or withdrawing approval retires earlier files containing that test. Retired files say Out of date. Do not import., have no import prompt or Download again, and identify the affected tests. Other approved tests in a mixed file return to To download for a clean replacement. Existing incompatible download history is also checked when loading saved browser data. The earlier-file warning explains that a later snapshot will return an already-imported rejected update to review; this behavior has a browser regression check.
3. Changing a choice or wording clears its old note. Earlier note appears above an empty note box for deliberate reuse. Save preserves the old note in History; new approvals contain only the current, deliberately supplied note.
4. Partly decided tests explain that approval requires a choice on every change, and name the waiting fields, including set-aside fields.
5. An unchanged test has no standalone Other fields heading. A sole carried choice can return to its originating list without prompting or saving, including with browser Back; ordinary editing and other unsaved-test cases retain warnings. Confirmation uses one dated line. All-caught-up text counts tests, not changes.

Browser cases cover every requested item 1–4 and the small fixes, including cancelled edits, withdrawn files observed in later snapshots, mixed-file clean replacements, unique filenames, persisted retired-file status, note provenance, and missing-approval explanations. Earlier workflow, Excel, navigation, focus, and phone regressions remain in the full suite. Current results and exact tested source/test hashes appear in verification.json.

Retired history keeps the original downloaded payload and filename for audit. It cannot retract a file already on a user's computer or in OLSD. Reverting a draft does not silently make a retired file importable again; make a fresh approved download instead. A matching snapshot remains a dated observation, not proof of live publication.

Release validation: 379 browser checks passed, with no JavaScript errors. The 2-click save, 5-click single-download, and 7-click 32-name paths remain unchanged.
