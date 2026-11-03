# OLSD workflow prototype — revision 5

Static sample-data prototype for independent usability and workflow review. Open `index.html` or use the website preview. No live Epic, OLSD, Connect, Helix, or pin connections are made.

- `review.html`: glossary, walkthrough, screenshots, and production gaps.
- `source.txt`: complete single-file client source in the published site.
- `check_workflows.py`: browser regressions organized by the independent reviewer’s item numbers.
- `verification.json`: verification date, exact tested source commit, source/test-script hashes, and every passing check.
- `REVIEW_CHANGES.md`: implementation notes for the independent review.

The browser storage key changed to `olsd-workflow-prototype-v5-review-20261102`, so returning reviewers receive the new sample catalog. The demo now contains 306 records for sorting, filtering, search, and pagination.

Choose **Reset demo** before a walkthrough. Role and reset controls are available in the top-bar menu on desktop and phones and in Source & system. Decisions are explicit; export inclusion does not resolve open source changes. Keep choices with no OLSD change finish on save. Saved choices and approved changes have separate visible sections.

Downloads are named `.xlsx` sample files. Separate column selections require separate Excel files. File history records the browser’s download initiation, not proof that a user saved or imported the file. Do not import demo files into OLSD.

To run the checks, serve this folder locally, install Python Playwright/openpyxl and Chromium, then run:

```sh
python -m http.server 3000
python check_workflows.py
```

Set `OLSD_TEST_URL` for another server. Pass one item number, such as `python check_workflows.py 4`, to run a focused regression. Every wrong-results item 1–11 is covered; item 12 was intentionally absent from the review. The suite also covers items 13–29. Checks use isolated browser contexts and inspect exact decisions, source bases, approvals, download records, and Excel values.

GitHub Pages publishes the `gh-pages` branch from the repository root. No build dependencies are required. `app-script.js` is the maintainable source embedded in `index.html`; `build_prototype.py` is the local assembly helper and is not needed to serve the site.

Production gaps include authenticated server permissions, real source/snapshot adapters, scheduled checks, safe shared persistence, migration, clinical review, vendor import acceptance, and control-column semantics. Sample vendor control values now come from stored test metadata. Real values and blank handling still require validation with the vendor.
