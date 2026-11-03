# OLSD workflow demo — revision 8

Static prototype with 308 sample tests. Open `index.html` or the website preview. No live Epic, OLSD, Connect, Helix, or pin connections.

- `review.html`: short task list and production limits.
- `source.txt`: complete published HTML/JavaScript.
- `app-script.js`: maintainable client source embedded in the HTML.
- `check_workflows.py`: browser rules, regression checks, measured click targets, and Excel readback.
- `verification.json`: date, exact tested source commit, hashes, test-script link, and passing checks.
- `REVIEW_CHANGES.md`: redesign summary.

This update retains `olsd-workflow-prototype-v7-test-by-test-20261103`, so returning reviewers keep previously saved work. Reset, role, and demo-check controls are in the sample-data strip on every screen, including phones.

Choosing is never saving. Save is never approval. Every approval needs its own click. Exact saved catalog/Epic values and dates remain attached to approval records. Unexpected later changes invalidate affected approvals. Named Excel files download directly; the app records initiation, not proof of saving/import. Do not import sample files into OLSD.

Run the checks with Python Playwright, Chromium, and openpyxl installed:

```sh
python -m http.server 3000
python check_workflows.py
```

Set `OLSD_TEST_URL` to test another server. Pass a case name, such as `python check_workflows.py five-click-flow`, for a focused check. GitHub Pages publishes the `gh-pages` branch from the repository root. There is no server or build dependency for the site.

Follow-up controls: bulk Epic/OLSD/later choices; Save, Save and next, Save and exit; Previous/Next; linked app name. To approve and To download use initially empty checkboxes with Select all, and actions apply only to selected tests. Approval can be sent back to review; an existing approval can be withdrawn. The 308-test sample catalog and existing storage key are retained. See verification.json for the current check results.

Each test appears once in To review. Tests with several open fields appear first under More than one change; name-only and lab-only tests remain in their existing sections. Vitamin D (VITD) and Hemoglobin A1c (A1C) demonstrate simultaneous name and laboratory changes. Opening either shows all outstanding fields together.

Review one by one follows displayed order, or only checked tests when selected. A multi-change test checkbox selects its eligible name/lab changes; free text is never bulk-accepted. Partial choices can be saved, but approval waits for every open field. Save and next appears only after all visible questions have choices. Decide later sets aside the remaining unanswered fields while preserving choices already made.

Validation: see verification.json for the current full-suite result. Checks cover the supplied section 6 checklist: one row per test, section totals matching the To review tab, screen-order navigation, all questions together, Save and next waiting for all choices, and free text remaining open after bulk actions. See verification.json for the full-suite result, tested commit, and source/test hashes.

Free-text-only tests can be selected for Review one by one; bulk actions remain limited to name and lab changes. Other changes name their field and direct the reviewer to open the test. Keyboard hints on multi-change tests follow the first unanswered field and disappear when all are chosen.

Saved choices and set-aside fields are now listed separately from the current OLSD entry. Change reopens saved answer cards without changing saved data; saving a changed approved choice withdraws its approval. Sent-back wording remains visible as Keep my saved wording.

Review one by one supports both review and approval lists, including selected subsets. Review walks use Save and next, then Save and finish; approval walks use Approve and next, then return to the list with Go to To download. Neither path creates a file automatically. Ordinary test editing keeps Save primary. Back links identify the originating list or search.

Inline choices preserve row selection. Selection bars retain Save for pending work. Kept/Set aside lists show field decisions and notes, and lab filters show visible/total counts. On phones the compact save bar keeps the main action visible, with secondary actions under More. Every requested item in sections 1 and 2 of the e89992d review has a browser regression case; worklist and wording/phone fixes also have checks.

Release validation: 302 browser checks passed, with no JavaScript errors. The measured 2-click save, 5-click single-file flow, and 7-click 32-name flow remain unchanged.
