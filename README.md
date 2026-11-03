# OLSD workflow demo — revision 7

Static prototype with 308 sample tests. Open `index.html` or the website preview. No live Epic, OLSD, Connect, Helix, or pin connections.

- `review.html`: short task list and production limits.
- `source.txt`: complete published HTML/JavaScript.
- `app-script.js`: maintainable client source embedded in the HTML.
- `check_workflows.py`: browser rules, regression checks, measured click targets, and Excel readback.
- `verification.json`: date, exact tested source commit, hashes, test-script link, and passing checks.
- `REVIEW_CHANGES.md`: redesign summary.

The storage key changed to `olsd-workflow-prototype-v7-test-by-test-20261103`. Returning reviewers receive fresh sample data. Reset, role, and demo-check controls are in the sample-data strip on every screen, including phones.

Choosing is never saving. Save is never approval. Every approval needs its own click. Exact saved catalog/Epic values and dates remain attached to approval records. Unexpected later changes invalidate affected approvals. Named Excel files download directly; the app records initiation, not proof of saving/import. Do not import sample files into OLSD.

Run the checks with Python Playwright, Chromium, and openpyxl installed:

```sh
python -m http.server 3000
python check_workflows.py
```

Set `OLSD_TEST_URL` to test another server. Pass a case name, such as `python check_workflows.py five-click-flow`, for a focused check. GitHub Pages publishes the `gh-pages` branch from the repository root. There is no server or build dependency for the site.

Follow-up controls: bulk Epic/OLSD/later choices; Save, Save and next, Save and exit; Previous/Next; linked app name. To approve and To download use initially empty checkboxes with Select all, and actions apply only to selected tests. Approval can be sent back to review; an existing approval can be withdrawn. This revision uses a new storage key so returning reviewers receive the 308-test sample catalog. See verification.json for the current check results.

Each test appears once in To review. Tests with several open fields appear first under More than one change; name-only and lab-only tests remain in their existing sections. Vitamin D (VITD) and Hemoglobin A1c (A1C) demonstrate simultaneous name and laboratory changes. Opening either shows all outstanding fields together.

Review one by one follows displayed order, or only checked tests when selected. A multi-change test checkbox selects its eligible name/lab changes; free text is never bulk-accepted. Partial choices can be saved, but approval waits for every open field. Save and next appears only after all visible questions have choices. Decide later sets aside the remaining unanswered fields while preserving choices already made.

Validation: the full updated browser suite passes 231 checks with no JavaScript errors. The separate one-row-per-test instructions (including section 6) were not included in the linked patch artifact, so their exact checklist is pending. This revision is prepared locally and has not been published.
