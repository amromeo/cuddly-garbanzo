# Revision 6 — choose, save, approve, download

This redesign implements “Make it obvious to use,” reviewed against baseline 15cf047.

- Four worklist views: To review, To approve, To download, All tests. The editor review count excludes lab-name blockers and set-aside tests. All tests has Kept wording, Set aside, Downloaded, Done, and Waiting filters.
- Simple name/lab choices happen inline with actual old/new values. Selection covers the complete section, including unloaded rows. Bulk actions never apply to free text.
- All choices remain browser-memory-only until Save. Save never approves. A saved batch has Undo until a later action makes undo unsafe.
- The separate group-review page, include checkboxes, sort/page-size controls, dark sidebar, duplicate status columns, and always-on disabled action bars are removed.
- A test asks one question with actual-value cards. Writing is offered only for names and conditions. Other catalog content stays visible with Edit actions. Up-to-date tests are normal readable catalog entries.
- Saved changes have a separate explicit Approve action. Approval keeps exact OLSD/Epic values, dates, actor, and time. Already approved tests are not reapproved by default.
- Downloading is one action for one or several named Excel files, with no confirmation or chooser. Each initiated file is recorded separately. The next step is to import into OLSD; sample files must not be imported into a real catalog.
- Unexpected catalog/Epic changes return tests to review. Matching expected downloaded values make a test done. A matching snapshot remains a dated observation, not proof of real-time publication.
- Decide later removes the test from To review after Save. A later Epic change returns it, with the prior decision and note visible. Review now can also reopen it deliberately.
- Notes, exact unsaved before/after values, navigation warnings, line/word highlights, request-help placeholders, role guards, URLs, Back, focus handling, and administrator return links remain.
- One sample-data strip holds the role, Reset, and demo-check controls on desktop and phone. System fonts use 15px body text and at least 13px labels; mobile targets are at least 44px.
- Shortcuts 1/2 choose and Ctrl/Cmd+S saves. The reviewer guide is a short task list.

Automated checks measure the 2-click save, 5-click single download, and 6-click 32-name download paths. `verification.json` records the results, tested source commit, and code/test hashes. The new storage key is `olsd-workflow-prototype-v6-choose-save-20261102`.
