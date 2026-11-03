# Revision 7 — one row per test

This redesign implements “Make it obvious to use,” reviewed against baseline 15cf047.

- Four worklist views: To review, To approve, To download, All tests. The editor review count excludes lab-name blockers and set-aside tests. All tests has Kept wording, Set aside, Downloaded, Done, and Waiting filters.
- Simple name/lab choices happen inline with actual old/new values. Selection covers the complete section, including unloaded rows. Bulk actions never apply to free text.
- All choices remain browser-memory-only until Save. Save never approves. A saved batch has Undo until a later action makes undo unsafe.
- The separate group-review page, include checkboxes, sort/page-size controls, dark sidebar, duplicate status columns, and always-on disabled action bars are removed.
- A test shows all outstanding questions together with actual-value cards. Writing is offered only for names and conditions. Other catalog content stays visible with Edit actions. Up-to-date tests are normal readable catalog entries.
- Saved changes have a separate explicit Approve action. Approval keeps exact OLSD/Epic values, dates, actor, and time. Already approved tests are not reapproved by default.
- Downloading is one action for one or several named Excel files, with no confirmation or chooser. Each initiated file is recorded separately. The next step is to import into OLSD; sample files must not be imported into a real catalog.
- Unexpected catalog/Epic changes return tests to review. Matching expected downloaded values make a test done. A matching snapshot remains a dated observation, not proof of real-time publication.
- Decide later removes the test from To review after Save. A later Epic change returns it, with the prior decision and note visible. Review now can also reopen it deliberately.
- Notes, exact unsaved before/after values, navigation warnings, line/word highlights, request-help placeholders, role guards, URLs, Back, focus handling, and administrator return links remain.
- One sample-data strip holds the role, Reset, and demo-check controls on desktop and phone. System fonts use 15px body text and at least 13px labels; mobile targets are at least 44px.
- Shortcuts 1/2 choose and Ctrl/Cmd+S saves. The reviewer guide is a short task list.

Automated checks measure the 2-click save, 5-click single download, and 7-click 32-name download paths. `verification.json` records the results, tested source commit, and code/test hashes. The new storage key is `olsd-workflow-prototype-v7-test-by-test-20261103`.

## Follow-up controls

- Bulk review offers Use Epic, Keep what is in the OLSD, and Decide later, all staged until Save.
- The test editor offers Save, Save and next, Save and exit, and Previous/Next navigation. The linked app name returns to the worklist with the unsaved-work guard.
- To approve and To download start with empty checkbox selections. Select some or Select all. Approve or send selected tests back to review; download or withdraw approval for selected tests. Unchecked tests remain unchanged.
- The explicit approval selection adds one click to the 32-name path (7 total). Current results are recorded in verification.json.

## One-row-per-test patch

Applied the supplied Claude artifact patch with git apply against 96184ae. There are now 308 sample tests, including VITD and A1C with two open fields each. The initial editor worklist has 45 tests to review: 2 with multiple changes, 32 name-only, and 11 lab-only; 0 to approve and 1 to download.

- Multi-change tests appear once, first, with each outstanding field inside their row.
- Test-level selection covers eligible name/lab fields; section selection still covers unloaded rows. Bulk counts distinguish tests from field choices.
- Review one by one follows displayed order or the selected subset. Previous revisits saved tests.
- The test editor shows all open fields together, chosen counts, and remaining work. Partial saves retain unresolved work and cannot enable approval. Save and next waits for a choice on every question.
- Decide later defers unanswered fields and preserves prior choices.
- The storage key changed to olsd-workflow-prototype-v7-test-by-test-20261103 for fresh sample data.
- Follow-up fixes retain checkbox focus and use singular test wording in bulk counts.

Validation: the full updated browser suite passes 231 checks with no JavaScript errors. The separate one-row-per-test instructions (including section 6) were not included in the linked patch artifact, so their exact checklist is pending. This revision is prepared locally and has not been published.
