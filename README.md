# OLSD Posit Connect pilot

R/Shiny implementation of the catalog workflow, with server-owned choices, approvals, snapshots, export records, and history. The approved public JavaScript prototype remains in the repository root as the behavior reference. This application is a separate deployment; it starts without sample catalog records.

The implementation runs locally with versioned folder pins. Live Connect authentication, institutional Helix access, real importer acceptance, and the single-process hosting arrangement still require institutional validation. The original prototype's 498 checks are not a certification of this backend; see `verification.json` for the pilot's own checks.

## Run locally

From this directory, use R 4.5.3 and restore the lockfile:

```r
install.packages("renv")
renv::restore(prompt = FALSE)
```

Set `OLSD_DATA_DIR` to a persistent directory outside the checkout (the local default is the ignored `local-pins/` directory), then run:

```sh
Rscript -e 'renv::load();shiny::runApp(".", host="127.0.0.1", port=3010)'
Rscript -e 'renv::load();source("tests/run.R")'
OLSD_USE_RENV=true RSCRIPT=Rscript python tests/run_browser.py
```

Browser checks require Python Playwright and Chromium. They start a separate process on port 3011, generate synthetic fixtures in a temporary directory, and shut it down after testing. They do not connect to an institutional source.

Local mode uses the explicit identity `local-operator`. Hosted mode takes identity from the authenticated Shiny session and fails closed when identity is absent. Local identity overrides do not apply on Connect.

## Application boundaries

- `R/core.R` owns workflow transitions. Browser requests supply field choices and test IDs; they cannot submit approval records or replace the saved state.
- `R/storage.R` owns versioned persistence, stale-revision rejection, a single writer-session lease, idempotent request receipts, and durable-write verification. The application holds a process-lifetime file lock. Connect must also enforce one process and one replica.
- `R/sources.R` validates snapshots and identities. `jobs/refresh_epic.R` publishes source versions only. The app applies new versions through its sole state writer, postponing application during unsaved work.
- `R/exports.R` renders approved values into individual Excel files and validates approval again at download. File preparation alone does not create history. History records initiation, not proof that a browser saved a file or that OLSD imported it.
- `R/migration.R` creates a review candidate from the supplied schema 7/8 state. Legacy approvals are archived, never promoted into current approval state.

The state is a versioned RDS object containing keyed test/field records, mapping tables, immutable approval snapshots, export records, and an audit log. `schema` and `revision` are separate. A storage adapter can replace pins later without changing workflow commands. Source snapshots and file artifacts live in separate pins, referenced from the state. A pin revision is not a database transaction; this pilot deliberately supports one active writer.

The root prototype’s browser storage is never read or migrated. No real source data, SQL, credentials, or generated workbooks belong in this repository.

## Production rollout

Follow [DEPLOYMENT.md](DEPLOYMENT.md). Deploy development first, run the read-only comparisons, validate vendor import behavior, and then permit the supervised pilot export/import cycle. Deployment scripts select only application code, dependencies, and assets; tests, local data, and credentials are excluded.

Deferred features remain concurrent editors, automatic OLSD website collection, and hash/identifier round-trip verification in the vendor catalog. Internal file hashes already protect artifact integrity, but they are not injected into OLSD.

One Epic procedure may feed multiple OLSD entries. Source normalization expands distinct OLSD links and retains each link label; approvals and wording choices stay per OLSD ID. The shared Epic name is source context, and does not automatically replace specimen-specific OLSD names.

An OLSD entry can also have multiple Epic procedures. The link table is keyed by `(OLSD ID, Procedure ID)`; the worklist remains keyed by OLSD ID. All linked procedures are displayed on the test page. Identical sources can supply common values; conflicting sources preserve the proposal and enter administrator procedure-assignment review. An administrator explicitly selects one primary procedure to drive updates. Other linked procedures remain available as references. Assignment changes invalidate approval and unconfirmed files; losing the primary link returns the entry to assignment review without selecting a replacement automatically.

Missing Epic display names are retained in `normalize_helix(...)$issues` and the versioned source pin. Linked entries without a usable primary source appear in **Source issues**, outside the normal review queue, with OLSD content preserved and approval blocked. Unlinked procedures remain in `excluded`. A complete primary procedure may be explicitly selected while incomplete alternate links remain visible. A later corrected source clears the missing-name issue and resumes normal review; placeholder names are never exported.

Lab mapping controls are populated from distinct Epic sections, observed OLSD laboratory/category values, and saved mappings. Selecting an existing section prefills its saved mapping. Administrators may explicitly enter a new public name or category; no name similarity is used to infer a mapping. No separate unique-name export is required.

The worklist initially renders 50 matching entries, with Show 50 more for additional rows. Counts, section selection, bulk actions, and review queues still operate on all matching entries. Status/count calculations are cached until saved state changes, and unchanged state-pin versions are served from memory. Background pin polling runs on timers rather than navigation/input invalidations.

Run the synthetic 1,542-entry navigation/selection check with `OLSD_BROWSER_SCALE=true OLSD_USE_RENV=true python tests/run_browser.py`. Its timings describe the test environment, not a guaranteed institutional response time.

Lab/category choices decode HTML and entities before splitting values, preventing font/style fragments from becoming options. Case/whitespace-only variants are consolidated for the selector; differently worded names remain separate. Raw snapshot values and saved mappings are not rewritten by this display cleanup. Saving a mapping is still explicit. This uses the `xml2` dependency in the lockfile.

To prepare a lab-name review file, stop Shiny and run `source("scripts/export_lab_review.R")` from the project root in the same R session/data-folder configuration. It writes `lab-name-review.xlsx` with raw OLSD lab values and counts, distinct Epic sections, and saved mappings. It does not query the warehouse or change any pins. Raw HTML is preserved for inspection; no SQL or credentials are included. The workbook is ignored by Git.
