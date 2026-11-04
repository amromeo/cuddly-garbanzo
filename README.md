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
