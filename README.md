# OLSD workflow demo — revision 9

Static prototype with 308 sample tests. Open `index.html` or the website preview. No live Epic, OLSD, Connect, Helix, or pin connections.

- `review.html`: tasks to try, screenshots, terminology, and production limits.
- `source.txt`: complete published HTML/JavaScript.
- `app-script.js`: maintainable client source embedded in the HTML.
- `check_workflows.py`: browser regression checks, measured click targets, and Excel readback.
- `verification.json`: date, exact tested source commit, hashes, check results, and test-script link.
- `REVIEW_CHANGES.md`: changes requested against commit 32260a9.

The existing storage key, `olsd-workflow-prototype-v7-test-by-test-20261103`, is retained. This update preserves previously saved browser work. Reset, role, and demo-check controls remain available on desktop and phone.

Each test appears once in To review. Tests with multiple open changes appear first, with all fields visible on one test page. Bulk actions affect eligible name/lab changes and leave free text open. Choosing never saves; saving never approves. Approval and downloading remain separate deliberate actions.

Saved fields appear once in a section named Ready for approval, Approved, or Your saved choices. Each row compares In OLSD now with After import (or Kept), shows its note, and has one Change button. Change replaces the row with answer cards; Cancel restores the saved row without changing other unsaved fields. Leaving the test closes reopened cards. Other fields excludes fields already shown above.

A matching later snapshot shows Confirmed in OLSD with its date, rather than Kept or Change. Edit can start a new draft. A matching snapshot is an observation, not proof of real-time publication.

Keep my saved wording is offered only when saved wording differs from both Epic and OLSD, including after an OLSD change. Source notes say You saved and mention Epic only if Epic changed. Sent-back wording equal to Epic uses normal Epic/Keep choices; genuinely different saved wording remains explicit.

Review/approval walkthroughs follow displayed order or selected tests. Review uses Save and next, then Save and finish; the ending counts saved tests and any that still need a choice. Approval uses Approve and next and returns to the list for downloads. Back links name the originating list or search. Phone bars keep the main action visible and place secondary actions behind More.

Opening the sole unsaved test from its worklist row carries the choice into the editor without saving or prompting. All other navigation involving unsaved tests retains the warning. Inline choices preserve ticks, and selection bars retain Save for unsaved work.

Named Excel files download directly, with per-file history. The app records browser initiation, not proof of saving/import. Do not import sample files into OLSD. Approvals retain exact OLSD/Epic values and dates; later unexpected source changes invalidate affected approvals. Production limits and vendor-import questions remain in the guide.

Run checks with Python Playwright, Chromium, and openpyxl installed:

```sh
python -m http.server 3000
python check_workflows.py
```

Set `OLSD_TEST_URL` to test another server. A case name, such as `python check_workflows.py once-3-cancel-change`, runs a focused check. GitHub Pages publishes `gh-pages` from the repository root; the site has no build or server dependency.

Release validation: 336 browser checks passed, with no JavaScript errors. Measured save/single-download/32-name paths remain 2/5/7 clicks.
