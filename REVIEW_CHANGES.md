# Revision 8 — saved choices and complete test walks

Addresses “OLSD prototype: next fixes,” reviewed at e89992d. The existing 308 sample tests, storage key, one-row-per-test grouping, and separate choose/save/approve steps are retained.

- Items 1–2: Your saved choices shows current OLSD, kept/proposed content, notes, and Change. Set aside names each deferred field and its Epic value. The catalog entry uses actual OLSD values. Opening Change has no saved effect; saving a changed approved choice withdraws approval, with a visible warning. Test pages offer Send back or Withdraw approval.
- Item 3: Sent-back content remains visible after reload in Keep my saved wording. Its worklist row shows the saved wording and opens the test rather than offering bulk replacement.
- Items 4–5: Selected/full approval walks offer Approve and next and a final return to the list, with Go to To download. Review walks end with Save and finish and a saved-test count. Files remain a separate deliberate action.
- Items 6–7: Back links use the originating list or search name, including after refresh. Save and next is primary during review walks once every field has a choice; Save remains primary in ordinary editing.
- Items 8–11: Inline choices preserve checked tests. Selection bars retain Save for unsaved choices. Kept/Set aside lists describe the fields, values, and notes. Filtered lists state the visible and total test counts.
- Items 12–15: Source-change headings name the field and show Was/Now for OLSD changes. Day ages use the correct singular/plural wording. Unsaved comparisons name the field once. Multi-change lines retain Unsaved and button highlights without repeating the choice text.
- Item 16: Phone save and selection bars keep the main action visible; More reveals secondary actions in a menu.

Each item in sections 1 and 2 has a browser check. Additional checks cover the worklist, wording, and phone changes; prior grouping, export, source invalidation, and approval checks are retained. Current results and exact hashes appear in verification.json.

## Earlier redesign

### Revision 7 — one row per test

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

The earlier revision added the supplied section 6 checklist: one row per test, section totals matching the To review tab, screen-order navigation, all questions together, Save and next waiting for all choices, and free text remaining open after bulk actions. See verification.json for the full-suite result, tested commit, and source/test hashes.

Free-text-only tests can be selected for Review one by one; bulk actions remain limited to name and lab changes. Other changes name their field and direct the reviewer to open the test. Keyboard hints on multi-change tests follow the first unanswered field and disappear when all are chosen.

Release validation: 302 browser checks passed, with no JavaScript errors. The measured 2-click save, 5-click single-file flow, and 7-click 32-name flow remain unchanged.
